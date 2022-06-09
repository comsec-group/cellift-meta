// Copyright 2022 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

/* common way to execute a testbench, sorry for the lame C-style macro */

/* used by multiple designs */
#include <chrono>

// Design-specific headers.
#include "testbench.h"

#ifdef LEADTICKS_DESIGN /* design overrides leadticks */
#define LEADTICKS LEADTICKS_DESIGN
#else
#define LEADTICKS 5
#endif

#ifdef TRAILTICKS_DESIGN /* design overrides TRAILTICKS */
#define TRAILTICKS TRAILTICKS_DESIGN
#else
#define TRAILTICKS 1
#endif


#define ARIANE_FLUSH_TICKS 256

#include <iostream>
#include <cassert>
#include <sstream>

static int get_sim_length_cycles(int lead_time_cycles)
{
  const char* simlen_env = std::getenv("SIMLEN");
  if(simlen_env == NULL) { std::cerr << "SIMLEN environment variable not set." << std::endl; exit(1); }
  int simlen = atoi(simlen_env);
  assert(lead_time_cycles >= 0);
  assert(simlen > 0);
  assert(simlen > lead_time_cycles);
  std::cout << "SIMLEN set to " << simlen << " ticks." << std::endl;
  return simlen - lead_time_cycles;
}

static const char *cl_get_tracefile(void)
{
#if VM_TRACE
  const char *trace_env = std::getenv("TRACEFILE"); // allow override for batch execution from python
  if(trace_env == NULL) { std::cerr << "TRACEFILE environment variable not set." << std::endl; exit(1); }
  return trace_env;
#else
  return "";
#endif
}

static inline long tb_run_ticks(Testbench *tb, int simlen, bool reset = false) {
  if (reset)
    tb->reset();

  auto start = std::chrono::steady_clock::now();
  tb->tick(simlen);
  auto stop = std::chrono::steady_clock::now();
  long ret = std::chrono::duration_cast<std::chrono::milliseconds>(stop - start).count();
  tb->tick(TRAILTICKS);
  return ret;
}
