// Reuse the audited kernels/model implementation while preserving old artifacts.
#define main previous_experiment_main
#include "../../src/experiment.cpp"
#undef main
#include <ctime>
#include <sstream>

double cpu_now(){timespec t;clock_gettime(CLOCK_PROCESS_CPUTIME_ID,&t);
    return t.tv_sec+t.tv_nsec*1e-9;}
double median(std::vector<double> v){std::sort(v.begin(),v.end());
    return v.size()%2?v[v.size()/2]:(v[v.size()/2-1]+v[v.size()/2])*.5;}
struct Measurement {std::string phase;int index,arm;double wall,cpu,loop,lib,cv;};

int main(int argc,char**argv){try{
    if(argc!=11)throw std::runtime_error(
        "usage: tradeoff KIND N SEED P POLICY H MODEL OUT BUDGET FIXED_ARM");
    std::string kind=argv[1],policy=argv[5];
    int n=std::stoi(argv[2]),seed=std::stoi(argv[3]),p=std::stoi(argv[4]);
    int horizon=std::stoi(argv[6]),budget=std::stoi(argv[9]),fixed=std::stoi(argv[10]);
    if(p<1||p>64||horizon<1||fixed<0||fixed>=K||budget<0||budget>K)
        throw std::runtime_error("invalid arguments");
    omp_set_dynamic(0);omp_set_num_threads(p);
    Workload work(kind,n,seed,p);Bandit model;
    const bool guided=policy=="prior"||policy=="budget";
    double load_w=0,load_c=0;
    if(guided){double w=now(),c=cpu_now();model.read(argv[7]);
        load_c=cpu_now()-c;load_w=now()-w;}
    work.run(0);work.run(0);
    std::vector<Measurement> rows;rows.reserve(horizon+40);
    auto measure=[&](int arm,const std::string& phase,int index){
        double c=cpu_now(),w=now();Obs ob=work.run(arm);
        double elapsed=now()-w,cpu=cpu_now()-c;
        rows.push_back({phase,index,arm,elapsed,cpu,ob.seconds,ob.lib,ob.cv});
        return ob;};
    double begin_w=now(),begin_c=cpu_now();
    std::vector<int> tested;int selected=fixed;
    Vec context{};std::vector<double> probes,libs,cvs;
    std::array<double,K> measured;measured.fill(1e100);
    if(policy!="fixed"&&policy!="reference"){
        for(int r=0;r<3;++r){Obs ob=measure(0,"probe",r);
            probes.push_back(ob.seconds);libs.push_back(ob.lib);cvs.push_back(ob.cv);}
        Obs probe{median(probes),median(libs),median(cvs),0};
        measured[0]=probe.seconds;tested.push_back(0);
        if(policy=="calibrate")selected=fixed;
        else{
            std::vector<int> order;
            if(guided){
                context=model.features(n,p,probe);
                std::vector<int> remaining(K);std::iota(remaining.begin(),remaining.end(),0);
                while(!remaining.empty()){
                    int a=model.choose(context,remaining,true);order.push_back(a);
                    remaining.erase(std::find(remaining.begin(),remaining.end(),a));}
                if(policy=="prior")selected=order[0];
                order.erase(std::remove(order.begin(),order.end(),0),order.end());
            }else{
                for(int a=1;a<K;++a)order.push_back(a);
                if(policy=="random"){
                    const char* val=std::getenv("TRADEOFF_RANDOM_SEED");
                    std::mt19937 gen(val?std::stoul(val):12345);
                    std::shuffle(order.begin(),order.end(),gen);}
            }
            int q=policy=="exhaustive"?K:budget;
            if(policy!="prior"){
                if(q<1)throw std::runtime_error("nonpositive candidate budget");
                for(int k=0;k<q-1;++k){int a=order.at(k);std::vector<double> values;
                    for(int r=0;r<3;++r)values.push_back(measure(a,"tune",r).seconds);
                    measured[a]=median(values);tested.push_back(a);}
                selected=std::min_element(measured.begin(),measured.end())-measured.begin();
            }
        }
    }
    double selection_c=cpu_now()-begin_c+load_c;
    double selection_w=now()-begin_w+load_w;
    double payload_w=now(),payload_c=cpu_now();
    std::vector<std::array<double,3>> prefixes;
    for(int t=0;t<horizon;++t){measure(selected,"payload",t);
        if(t+1==10||t+1==50||t+1==100||t+1==500)
            prefixes.push_back({double(t+1),now()-payload_w,cpu_now()-payload_c});}
    double payload_cpu=cpu_now()-payload_c,payload_wall=now()-payload_w;
    double actual=work.checksum();
    for(int i=0;i<n;++i)work.iteration(i);
    double expected=work.checksum();
    if(std::abs(actual-expected)>1e-8*std::max(1.,std::abs(expected)))
        throw std::runtime_error("parallel output mismatch");
    std::ofstream csv(argv[8]);csv<<std::setprecision(17);
    csv<<"phase,index,arm,wall_s,cpu_s,loop_s,lib,cv\n";
    for(auto& r:rows)csv<<r.phase<<','<<r.index<<','<<r.arm<<','<<r.wall<<','
        <<r.cpu<<','<<r.loop<<','<<r.lib<<','<<r.cv<<'\n';
    csv.close();
    std::ofstream summary(std::string(argv[8])+".summary.json");summary<<std::setprecision(17);
    summary<<"{\"selected_arm\":"<<selected<<",\"selection_wall_s\":"<<selection_w
        <<",\"selection_cpu_s\":"<<selection_c<<",\"payload_wall_s\":"<<payload_wall
        <<",\"payload_cpu_s\":"<<payload_cpu<<",\"load_wall_s\":"<<load_w
        <<",\"load_cpu_s\":"<<load_c<<",\"calibration_evaluations\":"
        <<std::count_if(rows.begin(),rows.end(),[](const Measurement&r){return r.phase!="payload";})
        <<",\"tested_arms\":[";
    for(size_t i=0;i<tested.size();++i){if(i)summary<<',';summary<<tested[i];}
    summary<<"],\"prefixes\":[";
    for(size_t i=0;i<prefixes.size();++i){if(i)summary<<',';
        summary<<"{\"horizon\":"<<prefixes[i][0]<<",\"payload_wall_s\":"<<prefixes[i][1]
               <<",\"payload_cpu_s\":"<<prefixes[i][2]<<'}';}
    summary<<"],\"checksum\":"<<actual<<",\"serial_checksum\":"<<expected<<"}\n";
    std::cerr<<std::setprecision(17)<<"CHECK "<<actual<<' '<<expected<<" SELECTED "
        <<selected<<" EVALUATIONS "<<tested.size()*3<<'\n';
    return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
