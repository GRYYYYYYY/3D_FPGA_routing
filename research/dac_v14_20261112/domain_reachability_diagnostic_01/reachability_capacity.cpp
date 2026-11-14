#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <memory>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
struct Npy {
 int fd;size_t bytes;void* mapped;const uint64_t* data;
 Npy(const char* path,const std::string& dtype,size_t count){
  fd=open(path,O_RDONLY);if(fd<0)throw std::runtime_error("open failed");struct stat st{};if(fstat(fd,&st))throw std::runtime_error("stat failed");bytes=st.st_size;
  mapped=mmap(nullptr,bytes,PROT_READ,MAP_PRIVATE,fd,0);if(mapped==MAP_FAILED)throw std::runtime_error("map failed");auto p=static_cast<const unsigned char*>(mapped);
  if(bytes<12||std::memcmp(p,"\x93NUMPY",6))throw std::runtime_error("npy magic");size_t base=p[6]==1?10:p[6]==2?12:0;if(!base)throw std::runtime_error("npy version");uint32_t len=p[8]|(uint32_t(p[9])<<8);if(base==12)len|=(uint32_t(p[10])<<16)|(uint32_t(p[11])<<24);
  std::string header(reinterpret_cast<const char*>(p+base),len);if(header.find(dtype)==std::string::npos||header.find("False")==std::string::npos||base+len+count*8!=bytes)throw std::runtime_error("npy layout");data=reinterpret_cast<const uint64_t*>(p+base+len);
 }
 ~Npy(){munmap(mapped,bytes);close(fd);}
};
int main(int argc,char**argv){try{
 if(argc<4)throw std::runtime_error("nodes edges case expected");bool unrestricted=false;const char* occupancy_path=nullptr;for(int i=4;i<argc;++i){std::string option=argv[i];if(option=="--unrestricted")unrestricted=true;else if(option=="--capacity"&&i+1<argc)occupancy_path=argv[++i];else throw std::runtime_error("unknown mode");}auto start=std::chrono::steady_clock::now();std::ifstream input(argv[3]);uint64_t n,m,stride,target,k,a;input>>n>>m>>stride>>target>>k;if(!input||n>=uint64_t(INT32_MAX)||target>=n||!stride)throw std::runtime_error("case header");std::vector<uint32_t> seeds(k);for(auto&x:seeds){input>>x;if(x>=n)throw std::runtime_error("seed");}input>>a;std::vector<uint8_t> allowed(n,0);for(uint64_t i=0,u;i<a;++i){input>>u;if(u>=n)throw std::runtime_error("allow");allowed[u]=1;}if(!input)throw std::runtime_error("case tail");
 Npy nodes(argv[1],"<i8",n*9),edges(argv[2],"<u8",m);std::unique_ptr<Npy> occupancy;if(occupancy_path)occupancy=std::make_unique<Npy>(occupancy_path,"<i8",n);const auto*e=edges.data;std::vector<uint64_t> offsets(n+1,0);uint64_t last=0;
 for(uint64_t i=0;i<m;++i){uint64_t u=(e[i]/stride)/n;if(u>=n||u<last)throw std::runtime_error("edge order");while(last<u)offsets[++last]=i;}while(last<n)offsets[++last]=m;
 std::vector<int32_t> parent(n,-2);std::vector<uint32_t> queue;queue.reserve(n);for(uint32_t u:seeds)if(parent[u]==-2){parent[u]=-1;queue.push_back(u);}uint64_t examined=0;size_t head=0;
 while(head<queue.size()&&parent[target]==-2){uint32_t u=queue[head++];for(uint64_t j=offsets[u];j<offsets[u+1];++j){uint32_t v=(e[j]/stride)%n;++examined;if(!unrestricted&&nodes.data[u*9+4]!=nodes.data[v*9+4]&&!allowed[u])continue;if(parent[v]==-2&&(!occupancy||occupancy->data[v]<nodes.data[v*9])){parent[v]=int32_t(u);queue.push_back(v);}}}
 bool found=parent[target]!=-2;std::vector<uint32_t> path;if(found){int32_t v=target;while(v>=0){path.push_back(v);v=parent[v];}std::reverse(path.begin(),path.end());}
 std::cout<<"{\"reachable\":"<<(found?"true":"false")<<",\"visited_nodes\":"<<queue.size()<<",\"examined_edges\":"<<examined<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<",\"path\":[";for(size_t i=0;i<path.size();++i){if(i)std::cout<<',';std::cout<<path[i];}std::cout<<"]}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
