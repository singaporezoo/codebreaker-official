//#define DEBUG

#include "mymanagerframework.h"
#include <vector>
#include <unordered_map>
#include <algorithm>
#include <cstdlib>
#include <cassert>
#include "adversaries/lib.h"

using namespace std;

constexpr int TESTCASE = 510370837,
                 WRITE = 849256539,
                  READ = 410973902,
                ANSWER = 167086295,
                  QUIT = 347829392,
               GOODBYE =  42424242;

#ifdef DEBUG
	#define TOO_MANY_WRITES "Too many writes"
	#define INVALID_WRITE "Invalid call to write"
	#define TOO_MANY_READS "Too many reads"
	#define INVALID_READ "Invalid call to read"
	#define WRONG_ANSWER "Wrong answer"
	#define INVALID_ANSWER "Invalid call to answer"
	#define NO_ANSWER "Exited without returning answer"
	#define CORRECT "Correct: %d signal(s) sent"
	#define SECURITY_VIOLATION "Security violation!"
#else
	#define TOO_MANY_WRITES "Not correct"
	#define INVALID_WRITE "Not correct"
	#define TOO_MANY_READS "Not correct"
	#define INVALID_READ "Not correct"
	#define WRONG_ANSWER "Not correct"
	#define INVALID_ANSWER "Not correct"
	#define NO_ANSWER "Not correct"
	#define CORRECT "Correct: %d signal(s) sent"
	#define SECURITY_VIOLATION "Security violation!"
#endif

int read_int_or_fail(FILE *f) {
	int i;
	if (fscanf(f, "%d", &i) != 1)
		result(0.0, SECURITY_VIOLATION);
	return i;
}

struct trie {
  trie *p = 0, *c[2] = {0, 0};
  int v[2] = {-1, -1};
  bool v3 = false;
  trie* child(int b) {
    if (!c[b])
      c[b] = new trie(), c[b]->p = this;
    return c[b];
  }
  void addValue(int x) {
    if (v[0] == x || v[1] == x || v3)
      return;
    if (v[1] != -1)
      v3 = true;
    else
      v[v[0] != -1] = x;
    if (p)
      p->addValue(x);
  }
  bool checkRequirement(int y, int z) {
    return !v3 && (v[0] == -1 || v[0] == y || v[0] == z) && (v[1] == -1 || v[1] == y || v[1] == z);
  }
  ~trie() {
    for (int b = 0; b < 2; b++)
      if (c[b])
        delete c[b];
  }
};

adversary *adv;
unordered_map<int, trie> trieRoots;

int MAX_N, G, W, use_partial_scoring, T, maxNumberWrites;

class communication_handler {
  private:
    int instance;
    int t = -1;
    trie *currentTrieNode;
    int g;
    int b;
    int numberWrites = 0;
    int numberReads = 0;
    vector<int> N, X;
    vector<int> permutation;
    vector<vector<int>> bits;
    bool answered;
    bool is_active;

    void wait_for_testcase() {
      int x;
      if(fscanf(fcommin[instance], "%d", &x) != 1)
        result(0.0, SECURITY_VIOLATION);
      if(x != TESTCASE)
        result(0.0, SECURITY_VIOLATION);
    }

    void handle_testcases_end() {
      if (t + 1 != T)
        result(0.0, SECURITY_VIOLATION);
    }

    void handle_encode_testcase_end() {
      if (t == -1)
        return;
      maxNumberWrites = max(maxNumberWrites, numberWrites);
      currentTrieNode->addValue(X[t]);
    }

    void handle_encode_testcase() {
      handle_encode_testcase_end();
      t++;
      if (t >= T)
        result(0.0, SECURITY_VIOLATION);
      g = G;
      numberWrites = 0;
      auto [n, x] = adv->testcase(T, t, MAX_N, G);
      assert(1 <= n && n <= MAX_N && 1 <= x && x <= n);
      N.push_back(n);
      X.push_back(x);
      currentTrieNode = &trieRoots[n];

      _write(fcommout[instance], "%d\n%d\n", n, x);
    }

    void handle_send() {
      if (t == -1)
        result(0.0, SECURITY_VIOLATION);

      if (numberWrites >= W)
        result(0.0, TOO_MANY_WRITES);

      b = read_int_or_fail(fcommin[instance]);
      if (b != 0 && b != 1)
        result(0.0, INVALID_WRITE);

      adv->send(instance, G, numberWrites, b);

      #ifdef DEBUG_
        fprintf(stderr, "[%d send %d]\n", instance, b);
      #endif
    }

    void handle_reply() {
      int r = adv->getReply(instance);

      #ifdef DEBUG_
        fprintf(stderr, "[%d reply %d, b was %d]\n", instance, r, b);
      #endif

      assert((r == 0 || r == 1) && (r == b || g >= G));
      g = r == b ? g + 1 : 0;
      bits[t].push_back(r);
      currentTrieNode = currentTrieNode->child(r);
      numberWrites++;

      _write(fcommout[instance], "%d\n", r);
    }

    void handle_decode_testcase_end() {
      if (t == -1)
        return;
      if (!answered)
        result(0.0, NO_ANSWER);
    }

    void handle_decode_testcase() {
      handle_decode_testcase_end();
      t++;
      if (t >= T)
        result(0.0, SECURITY_VIOLATION);
      numberReads = 0;
      answered = false;
      currentTrieNode = &trieRoots[N[permutation[t]]];

      _write(fcommout[instance], "%d\n", N[permutation[t]]);
    }

    void handle_read() {
      if (t == -1)
        result(0.0, SECURITY_VIOLATION);

      if (answered)
        result(0.0, INVALID_READ);
      if (numberReads >= (int) bits[permutation[t]].size())
        result(0.0, TOO_MANY_READS);

      _write(fcommout[instance], "%d\n", bits[permutation[t]][numberReads]);

      currentTrieNode = currentTrieNode->child(bits[permutation[t]][numberReads]);
      numberReads++;
    }

    void handle_answer() {
      if (t == -1)
        result(0.0, SECURITY_VIOLATION);

      if (answered)
        result(0.0, INVALID_ANSWER);
      answered = true;

      int y = read_int_or_fail(fcommin[instance]), z = read_int_or_fail(fcommin[instance]);

      if (y < 1 || y > N[permutation[t]] || z < 1 || z > N[permutation[t]])
        result(0.0, INVALID_ANSWER);
      if (!currentTrieNode->checkRequirement(y, z))
        result(0.0, WRONG_ANSWER);

      goodbye();
    }

    void goodbye() {
      int msg = (t == T - 1 ? -1 : GOODBYE);
      _write(fcommout[instance], "%d\n", msg);
    }

    bool adv_wants_to_reply() { return adv->getPhase(instance) == WANTS_TO_REPLY; }
    bool adv_waiting()        { return adv->getPhase(instance) == WAITING; }
    bool adv_ready()          { return adv->getPhase(instance) == READY; }
    bool adv_tired()          { return adv->getPhase(instance) == TIRED; }

  public:
    communication_handler(int instance) : instance(instance) {}

    void start_encode() {
      assert(bits.empty());
      bits.resize(T);
    }

    void new_encode_case() {
      _write(fcommout[instance], "1\n");
      wait_for_testcase();
      handle_encode_testcase();
      assert(adv_ready());
      is_active = true;
    }

    void poll_encode() {
      if(not adv_ready()) return;

      int type;
      int fscanf_return = fscanf(fcommin[instance], "%d", &type);

      // This can also happen if the user program is terminated because it runs out
      // of resources–however, in this case the manager verdict is suppressed, so
      // there is no harm in declaring this to be a security violation
      if (fscanf_return != 1)
        result(0.0, SECURITY_VIOLATION);

      switch(type) {
        case WRITE:
          handle_send();
          break;
        case READ:
          result(0.0, INVALID_READ);
        case ANSWER:
          result(0.0, INVALID_ANSWER);
        case QUIT:
          is_active = false;
          assert(adv_ready());
          adv->finish(instance);
          goodbye();
          break;
        default:
          result(0.0, SECURITY_VIOLATION);
      }
    }

    void maybe_reply() {
      if(adv_wants_to_reply()) handle_reply();
    }

    bool active() {
      return is_active;
    }

    void finish_encode() {
      handle_encode_testcase_end();
      handle_testcases_end();

      assert(N.size() == T and X.size() == T and bits.size() == T);
      assert(t + 1 == T);
    }

    void start_decode() {
      assert(permutation.empty());
      for (int i = 0; i < T; i++) permutation.push_back(i);
      random_shuffle(permutation.begin(), permutation.end());

      t = -1;
    }

    void new_decode_case() {
      _write(fcommout[instance], "2\n");
      wait_for_testcase();
      handle_decode_testcase();
    }

    bool poll_decode() {
      int type;
      int fscanf_return = fscanf(fcommin[instance], "%d", &type);

      if (fscanf_return != 1)
        result(0.0, SECURITY_VIOLATION);

      switch(type) {
        case READ:
          handle_read();
          break;
        case ANSWER:
          handle_answer();
          return false;
        case QUIT:
          result(0.0, "impossible");
        case WRITE:
          result(0.0, INVALID_WRITE);
        default:
          result(0.0, SECURITY_VIOLATION);
      }

      return true;
    }

    void finish_decode() {
      handle_decode_testcase_end();
      handle_testcases_end();
    }
};

float getScore() {
  if (maxNumberWrites >= 251) return 0.0;
  if (maxNumberWrites <= 100) return 1.0;

  float score;
  if(maxNumberWrites <= 110)       score = 285 - 2 * maxNumberWrites;
  else if (maxNumberWrites <= 140) score = 175 - maxNumberWrites;
  else if (maxNumberWrites <= 200) score = (245 - maxNumberWrites)/3.0;
  else                             score = (275 - maxNumberWrites)/5.0;
  return score / 85.0;
}

void handle_encode_step(vector<communication_handler> &handlers) {
  for(auto &h : handlers) h.start_encode();

  for(int i = 0; i < T; ++i) {
    adv->newRun();

    // The behaviour of the different instances may depend on each other, so
    // we have to interlace their executions properly
    for(auto &h : handlers)
      h.new_encode_case();

    for(int num_quit = 0; num_quit < num_instances;) {
      #ifdef DEBUG_
        fprintf(stderr, "encode, i = %d, num_quit = %d\n", i, num_quit);
      #endif

      for(auto &h : handlers) {
        if(not h.active()) continue;
        h.poll_encode();
        if(not h.active()) ++num_quit;
      }

      for(auto &h : handlers)
        h.maybe_reply();
    }

    adv->testcaseEnd();
    //next();
  }

  for(auto &h : handlers) h.finish_encode();

  #ifdef DEBUG_
    fprintf(stderr, "done with handle_encode_step\n");
  #endif
}

void handle_decode_step(vector<communication_handler> &handlers) {
  for(auto &h : handlers) h.start_decode();

  for(int i = 0; i < T; ++i) {
    #ifdef DEBUG_
      fprintf(stderr, "decode, i = %d\n", i);
    #endif

    // On the other hand, here we can just run the different instances after
    // each other since there is no interaction between them any more
    for(auto &h : handlers) {
      h.new_decode_case();
      while(h.poll_decode());
    }

    //next();
  }

  for(auto &h : handlers) h.finish_decode();
}

void check() {
  message_on_shutdown = true;

  int num_instances; fscanf(fin, "%d", &num_instances);
  assert(fscanf(fin, "%d %d %d %d %d", &MAX_N, &G, &W, &use_partial_scoring, &T) == 5);
  tell_cms(num_instances, T);
  open_pipes();

  srand(42 ^ MAX_N ^ G ^ W ^ use_partial_scoring ^ T);

  adv = create_adversary(fin, num_instances);

  vector<communication_handler> handlers;
  for(int i = 0; i < num_instances; ++i) handlers.emplace_back(i);

  handle_encode_step(handlers);
  delete adv;
  next();
  handle_decode_step(handlers);

  result(use_partial_scoring ? getScore() : 1.0, CORRECT, maxNumberWrites);
}
