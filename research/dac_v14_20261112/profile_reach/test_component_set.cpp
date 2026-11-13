#include "h3d_component_set.h"
#include <random>
#include <set>
#include <limits>
#include <iostream>
#include <cassert>
int main() {
 std::mt19937 rng(20261112);
 for(size_t trial=0;trial<50000;++trial) {
  std::set<int> a,b;
  for(int i=-50;i<250;++i){if(rng()%5) a.insert(i);if(rng()%3==0)b.insert(i);}
  if(trial%7==0)a.clear();
  if(trial%11==0)b.clear();
  if(trial%13==0){a.insert(std::numeric_limits<int>::max());a.insert(std::numeric_limits<int>::max()-1);a.insert(std::numeric_limits<int>::max()-2);a.insert(std::numeric_limits<int>::max()-3);}
  if(trial%17==0){a.insert(std::numeric_limits<int>::min());a.insert(std::numeric_limits<int>::min()+1);}
  std::vector<int> av(a.begin(),a.end()),bv(b.begin(),b.end());std::set<int> truth=a;truth.insert(b.begin(),b.end());std::vector<int> expected(truth.begin(),truth.end());
  for(bool compress:{false,true}) {
   H3dComponentSet x(av,compress);assert(x.size()==av.size());assert(x.stored_words()<=av.size());assert(x.merge(bv)==expected);assert(x.merge({})==av);
  }
 }
 H3dComponentSet dense({0,1,2,3,4},true);assert(dense.compressed()&&dense.stored_words()==2);
 H3dComponentSet sparse({0,2,4},true);assert(!sparse.compressed()&&sparse.stored_words()==3);
 std::cout<<"random_set_pairs=50000 plain_and_compact=100000 extrema_empty_dense_sparse=passed\n";
}
