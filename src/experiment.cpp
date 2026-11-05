#include <omp.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

// Algorithm IDs and order match LB4OMP's autoDLSPortfolio.
constexpr int K=12, D=6;
const int schedule_id[K]={1,2,101,4,3,108,102,111,112,113,114,116};
const char* arm_name[K]={"STATIC","SS","TSS","AutoLLVM","GSS","mFAC2",
                        "StaticSteal","AWFB","AWFC","AWFD","AWFE","mAF"};
using Vec=std::array<double,D>;
using Mat=std::array<Vec,D>;
double now(){return std::chrono::duration<double>(
    std::chrono::steady_clock::now().time_since_epoch()).count();}
struct alignas(64) Timer {double finish=0;};
struct Obs {double seconds,lib,cv,checksum;};

struct Workload {
    std::string kind; int n,seed,threads,maxiter;
    std::vector<double> a,b,c;
    std::vector<int> pixels,offset,edges;
    std::vector<long long> triangles;
    Workload(std::string kind_,int n_,int seed_,int p):
        kind(kind_),n(n_),seed(seed_),threads(p),maxiter(96+seed_*24){
        if(kind=="triad"){
            a.resize(n);b.resize(n);c.resize(n);
            for(int i=0;i<n;++i){b[i]=1.0+(i%97)*.001;c[i]=2.0+(i%71)*.001;}
        }else if(kind=="mandelbrot") pixels.resize(n);
        else if(kind=="triangle"){
            std::vector<std::vector<int>> adj(n);std::mt19937 gen(1907+seed);
            // Degree-skewed, undirected graph: a hub-biased prefix and uniform
            // endpoints. Deduplicate and sort before orienting by vertex ID.
            for(int i=0;i<n*24;++i){
                int u=gen()%n;
                int v=(i%3==0)?int(gen()%std::max(2,n/32)):int(gen()%n);
                if(u==v)continue;if(u>v)std::swap(u,v);adj[u].push_back(v);
            }
            offset.push_back(0);
            for(auto& row:adj){std::sort(row.begin(),row.end());
                row.erase(std::unique(row.begin(),row.end()),row.end());
                edges.insert(edges.end(),row.begin(),row.end());offset.push_back(edges.size());}
            triangles.resize(n);
        }else if(kind!="empty") throw std::runtime_error("unknown workload");
    }
    inline void mandel(int i){
            int side=int(std::sqrt(n));
            double shift=(seed%4)*.025;
            double cr=-2.0+3.0*(i%side)/side+shift;
            double ci=-1.2+2.4*(i/side)/side;
            double zr=0,zi=0;int j=0;
            while(j<maxiter && zr*zr+zi*zi<=4.0){
                double z=zr*zr-zi*zi+cr;zi=2*zr*zi+ci;zr=z;++j;}
            pixels[i]=j;
    }
    inline void triangle(int i){
            long long count=0;
            for(int q=offset[i];q<offset[i+1];++q){
                int v=edges[q],l=q+1,r=offset[v];
                while(l<offset[i+1] && r<offset[v+1]){
                    if(edges[l]==edges[r]){++count;++l;++r;}
                    else if(edges[l]<edges[r])++l;else ++r;}}
            triangles[i]=count;
    }
    inline void iteration(int i){
        if(kind=="triad") a[i]=b[i]+3.0*c[i];
        else if(kind=="mandelbrot")mandel(i);
        else if(kind=="triangle")triangle(i);
    }
    double checksum()const{
        if(kind=="triad")return std::accumulate(a.begin(),a.end(),0.0);
        if(kind=="mandelbrot")return std::accumulate(pixels.begin(),pixels.end(),0.0);
        return std::accumulate(triangles.begin(),triangles.end(),0.0);
    }
    Obs run(int arm,bool native_q=false){
        int chunk=arm==0?std::max(1,(n+threads-1)/threads):1;
        omp_set_schedule(static_cast<omp_sched_t>(native_q?4:schedule_id[arm]),
                         native_q?8:chunk);
        std::array<Timer,64> timers;
        double start=now();
        #pragma omp parallel num_threads(threads)
        {
            if(kind=="triad"){
                #pragma omp for schedule(runtime) nowait
                for(int i=0;i<n;++i)a[i]=b[i]+3.0*c[i];
            }else if(kind=="mandelbrot"){
                #pragma omp for schedule(runtime) nowait
                for(int i=0;i<n;++i)mandel(i);
            }else if(kind=="triangle"){
                #pragma omp for schedule(runtime) nowait
                for(int i=0;i<n;++i)triangle(i);
            }else{
                #pragma omp for schedule(runtime) nowait
                for(int i=0;i<n;++i)asm volatile("" : : "r"(i) : "memory");
            }
            timers[omp_get_thread_num()].finish=now()-start;
        }
        double elapsed=now()-start,mean=0,mx=0,var=0;
        for(int j=0;j<threads;++j){mean+=timers[j].finish;mx=std::max(mx,timers[j].finish);}
        mean/=threads;
        for(int j=0;j<threads;++j)var+=std::pow(timers[j].finish-mean,2);
        return {elapsed,1-mean/mx,std::sqrt(var/threads)/mean,0};
    }
};

struct Bandit{
    std::array<Mat,K> inv{};std::array<Vec,K> b{};
    Vec mean{},scale{};std::vector<int> reduced;
    int best_fixed=0;double alpha=.1;
    Bandit(){for(int a=0;a<K;++a)for(int j=0;j<D;++j)inv[a][j][j]=1;
        scale.fill(1);}
    void read(const std::string& path){
        if(path=="none")return;
        std::ifstream f(path);int d,k,m;f>>d>>k>>alpha>>best_fixed>>m;
        if(!f || d!=D || k!=K)throw std::runtime_error("invalid model header");
        reduced.resize(m);for(auto& a:reduced)f>>a;
        for(auto& v:mean)f>>v;for(auto& v:scale)f>>v;
        for(int a=0;a<K;++a){for(auto& row:inv[a])for(auto& v:row)f>>v;
            for(auto& v:b[a])f>>v;}
        if(!f)throw std::runtime_error("truncated model");
    }
    Vec features(int n,int p,const Obs& probe)const{
        Vec x={1,std::log2(n),std::log2(p),std::log2(probe.seconds),probe.lib,probe.cv};
        for(int j=1;j<D;++j)x[j]=(x[j]-mean[j])/scale[j];return x;
    }
    int choose(const Vec& x,const std::vector<int>& arms,bool greedy=false)const{
        double best=-1e100;int chosen=0;
        for(int a:arms){double estimate=0,variance=0;
            for(int i=0;i<D;++i){double v=0;
                for(int j=0;j<D;++j)v+=inv[a][i][j]*x[j];
                estimate+=v*b[a][i];variance+=x[i]*v;}
            double score=estimate+(greedy?0:alpha)*std::sqrt(std::max(0.,variance));
            if(score>best){best=score;chosen=a;}}
        return chosen;
    }
    void update(int a,const Vec& x,double reward){
        Vec v{};double denom=1;
        for(int i=0;i<D;++i){for(int j=0;j<D;++j)v[i]+=inv[a][i][j]*x[j];denom+=x[i]*v[i];}
        for(int i=0;i<D;++i){for(int j=0;j<D;++j)inv[a][i][j]-=v[i]*v[j]/denom;
            b[a][i]+=reward*x[i];}
    }
};

int main(int argc,char**argv){try{
    if(argc!=10)throw std::runtime_error(
        "usage: experiment KIND N SEED P POLICY HORIZON MODEL OUT FIXED_ARM");
    std::string kind=argv[1],policy=argv[5],modelpath=argv[7];
    int n=std::stoi(argv[2]),seed=std::stoi(argv[3]),p=std::stoi(argv[4]);
    int horizon=std::stoi(argv[6]),fixed=std::stoi(argv[9]);
    if(p<1||p>64||horizon<1||fixed<0||fixed>=K)throw std::runtime_error("invalid arguments");
    omp_set_dynamic(0);omp_set_num_threads(p);
    // Q-learning writes diagnostics to std::cout in unmodified upstream code.
    // Our machine-readable CSV is a separate file; never parse diagnostics as data.
    Workload w(kind,n,seed,p);Bandit bandit;bandit.read(modelpath);
    if(policy=="cold"){
        auto m=bandit.mean,s=bandit.scale;double a=bandit.alpha;
        bandit=Bandit();bandit.mean=m;bandit.scale=s;bandit.alpha=a;}
    std::vector<int> all(K);std::iota(all.begin(),all.end(),0);
    if(bandit.reduced.empty())bandit.reduced=all;
    w.run(0);w.run(0); // same two untimed useful warmups for every policy
    struct Row{int t,arm;double loop,decision,update,lib,cv,reward;};
    std::vector<Row> rows;rows.reserve(horizon);
    std::array<int,K> count{};std::array<double,K> total{},times{};
    times.fill(1e100);Obs probe{};Vec x{};
    double study_start=now();
    for(int t=0;t<horizon;++t){
        double decision_start=now();int a=0;
        if(t>0){
            if(policy=="fixed")a=fixed;
            else if(policy=="bestfixed")a=bandit.best_fixed;
            else if(policy=="exhaustive"){
                if(t<K)a=t;else a=std::min_element(times.begin(),times.end())-times.begin();
            }else if(policy=="ucb"){
                a=0;double best=-1e100;
                for(int j=0;j<K;++j){double v=count[j]?total[j]/count[j]+
                    .1*std::sqrt(2*std::log(t+1)/count[j]):1e10-j;
                    if(v>best){best=v;a=j;}}
            }else if(policy=="warm"||policy=="cold"||policy=="greedy"||policy=="reduced")
                a=bandit.choose(x,policy=="reduced"?bandit.reduced:all,policy=="greedy");
            else if(policy!="qlearn")throw std::runtime_error("unknown policy");
        }
        double decision=now()-decision_start;
        // Native upstream Q-learning includes its dispatch/learning time in loop.
        Obs ob=w.run(a,policy=="qlearn");
        double update_start=now();
        if(t==0){probe=ob;x=bandit.features(n,p,probe);}
        double reward=std::clamp(-std::log(ob.seconds/probe.seconds)/std::log(4.),-1.,1.);
        if(policy=="warm"||policy=="cold"||policy=="reduced")bandit.update(a,x,reward);
        ++count[a];total[a]+=reward;if(t<K)times[a]=ob.seconds;
        double update=now()-update_start;
        rows.push_back({t,policy=="qlearn"?-1:a,ob.seconds,decision,update,ob.lib,ob.cv,reward});
    }
    double study_wall=now()-study_start;
    double measured=w.checksum();
    // Exact same operations in serial provide an output-equivalence check.
    for(int i=0;i<n;++i)w.iteration(i);
    double expected=w.checksum();
    if(std::abs(measured-expected)>1e-8*std::max(1.,std::abs(expected)))
        throw std::runtime_error("parallel result mismatch");
    std::ofstream out(argv[8]);out<<std::setprecision(17);
    out<<"t,arm,loop_s,decision_s,update_s,lib,cv,reward\n";
    for(auto& r:rows)out<<r.t<<','<<r.arm<<','<<r.loop<<','<<r.decision<<','
        <<r.update<<','<<r.lib<<','<<r.cv<<','<<r.reward<<'\n';
    out.close();std::cerr<<std::setprecision(17)<<"CHECK "<<measured<<' '<<expected
        <<" WALL "<<study_wall<<" N "<<n<<" P "<<p<<'\n';
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}}
