#include <bits/stdc++.h>
#define INF (1LL<<62)
using namespace std;
typedef long long ll;
typedef pair<ll,int> ii;
typedef pair<int,ll> ii2;
typedef pair<int,int> ii3;
set <ii3> s;
vector <ll> dist;
priority_queue<ii,vector<ii>,greater<ii> >pq;
vector <ii2> adj[200005];
int p,pathv[200005];
bitset <200005> vis,used;
int n,m,p1,p2;
ll w;
ll dijkstra(int st){
	for(int x=0;x<=n;x++) dist.push_back(INF);
	dist[st]=0ll;
	pq.push(ii(0ll,st));
	vis.reset();
	while(!pq.empty()){
		ii front=pq.top();
		pq.pop();
		int v=front.second;
		if(v==pathv[p-1]) return dist[pathv[p-1]];
		if(vis[v]) continue;
		vis[v]=1;
		for(int i=0;i<int(adj[v].size());i++){
			if(dist[adj[v][i].first]>dist[v]+adj[v][i].second){
				dist[adj[v][i].first]=dist[v]+adj[v][i].second;
				pq.push(ii(dist[adj[v][i].first],adj[v][i].first));
			}
		}
	}
	return -1ll;
}
void fail(string str){
	printf("0\n%s\n",str.c_str());
	exit(0);
}
int main(int argc, char* argv[]){
	FILE *uout=fopen(argv[2],"r");
	freopen(argv[1],"r",stdin);
	scanf("%d %d",&n,&m);
	char ch;
	while(fscanf(uout,"%c",&ch)>0){
		if(ch==' '||ch=='\n') break;
		if(ch<'0'||ch>'9') fail("Invalid output");
		p=p*10+(ch-'0');
		if(p>n) fail("Invalid output");
	}
	if(p<2||p>n) fail("Invalid output");
	for(int x=0;x<p;x++){
		while(fscanf(uout,"%c",&ch)>0){
			if(ch==' '||ch=='\n') break;
			if(ch<'0'||ch>'9') fail("Invalid output");
			pathv[x]=pathv[x]*10+(ch-'0');
			if(pathv[x]>n) fail("Invalid output");
		}
		if(pathv[x]==0) fail("Invalid output");
	}
	used[pathv[0]]=1;
	for(int x=1;x<p;x++){
		if(used[pathv[x]]) fail("Some intersection visited twice");
		used[pathv[x]]=1;
		s.insert(ii3(pathv[x],pathv[x-1]));
	}
	ll ans=0ll;
	int ecnt=0;
	for(int x=0;x<m;x++){
		scanf("%d %d %lld",&p1,&p2,&w);
		adj[p1].push_back(ii2(p2,w));
		adj[p2].push_back(ii2(p1,w));
		if(s.find(ii3(p1,p2))!=s.end()||s.find(ii3(p2,p1))!=s.end()){
			ans+=w;
			ecnt++;
		}
	}
	int S, node;
	scanf("%d", &S);
	for (int x=0;x<S;x++){
		scanf("%d", &node);
		if (!used[node]) fail("Some intersections not visited");
	}
	if(ecnt!=p-1) fail("Some pair of consecutive intersections not linked by a road");
	if(dijkstra(pathv[0])!=ans) fail("Not shortest path");
	printf("1\n");
}

