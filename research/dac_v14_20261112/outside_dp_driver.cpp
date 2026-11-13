#include "h3d_independent_plan.h"
#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
int main(){
    size_t count;std::cin>>count;std::cout<<std::setprecision(17);
    for(size_t test=0;test<count;++test){
        size_t n,m,prior_count;std::cin>>n>>m>>prior_count;std::vector<double> opening(m);for(auto& v:opening)std::cin>>v;
        std::vector<t_h3d_plan_leaf> leaves;
        for(size_t i=0;i<n;++i){int pin,x,y;size_t k;double outside;std::cin>>pin>>x>>y>>outside>>k;t_h3d_plan_leaf leaf{pin,x,y,{}};if(outside>=0)leaf.outside_cost=outside;for(size_t j=0;j<k;++j){size_t c;double b;std::cin>>c>>b;leaf.candidates.push_back({c,b});}leaves.push_back(leaf);}
        std::vector<std::pair<int,size_t>> prior;for(size_t i=0;i<prior_count;++i){int pin;size_t channel;std::cin>>pin>>channel;prior.emplace_back(pin,channel);}
        for(int mode=0;mode<2;++mode){auto result=mode ? h3d_plan_independent(leaves,opening) : h3d_plan_partition(leaves,opening);double previous=0.;if(mode){for(const auto& leaf:leaves)previous+=h3d_assignment_cost({leaf},opening,prior);}else previous=h3d_assignment_cost(leaves,opening,prior);std::cout<<"PLAN "<<test<<' '<<mode<<' '<<result.cost<<' '<<previous<<' '<<result.groups<<' '<<result.outside_leaves<<' '<<result.assignment.size();for(auto a:result.assignment)std::cout<<' '<<a.first<<' '<<a.second;std::cout<<'\n';}
    }return !std::cin;
}
