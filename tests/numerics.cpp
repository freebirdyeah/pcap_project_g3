#define main experiment_cli_main
#include "../src/experiment.cpp"
#undef main
#include <cassert>

int main(){
    Bandit b;Vec x={1,2,-1,.5,0,3};double norm=0;
    for(double z:x)norm+=z*z;
    b.update(3,x,.7);
    for(int i=0;i<D;++i)for(int j=0;j<D;++j)
        assert(std::abs(b.inv[3][i][j]-((i==j?1.:0.)-x[i]*x[j]/(1+norm)))<1e-12);
    for(int i=0;i<D;++i)assert(std::abs(b.b[3][i]-.7*x[i])<1e-12);
    assert(b.choose(x,{3},false)==3);
    // Independent brute-force triangle check for a tiny generated graph.
    Workload w("triangle",40,2,2);
    for(int i=0;i<w.n;++i)w.iteration(i);
    long long brute=0;
    auto edge=[&](int u,int v){return std::binary_search(w.edges.begin()+w.offset[u],
        w.edges.begin()+w.offset[u+1],v);};
    for(int i=0;i<40;++i)for(int j=i+1;j<40;++j)for(int k=j+1;k<40;++k)
        if(edge(i,j)&&edge(j,k)&&edge(i,k))++brute;
    assert(w.checksum()==brute);
    omp_set_dynamic(0);
    for(int p:{2,4})for(int arm=0;arm<K;++arm){
        std::vector<int> visits(10003,0);
        omp_set_num_threads(p);
        omp_set_schedule(static_cast<omp_sched_t>(schedule_id[arm]),arm==0?2501:1);
        #pragma omp parallel for schedule(runtime)
        for(int i=0;i<10003;++i){
            #pragma omp atomic update
            visits[i]++;
        }
        for(int x:visits)assert(x==1);
    }
    std::cout<<"matrix update and independent triangle verification passed\n";
}
