// See LICENSE for license details.

//**************************************************************************
// Median filter bencmark
//--------------------------------------------------------------------------
//
// This benchmark performs a 1D three element median filter. The
// input data (and reference data) should be generated using the
// median_gendata.pl perl script and dumped to a file named
// dataset1.h.

#include "util.h"

#include "median.h"

//--------------------------------------------------------------------------
// Input/Reference Data

#include "dataset1.h"

//--------------------------------------------------------------------------
// Main

int main( int argc, char* argv[] )
{
  int results_data[DATA_SIZE];

#if PREALLOCATE
  // If needed we preallocate everything in the caches
  median( DATA_SIZE, input_data, results_data );
#endif

  setStats(1);
  median( DATA_SIZE, input_data, results_data );
  setStats(0);

  // Signal that the program is complete.
  #define xstr(s) str(s)
  #define str(s) #s
  asm volatile ("li t0, "xstr(STOP_SIGNAL_ADDR)"; " "sw x0, (t0);\n\t" ::: "t0");
  // Busy wait for the simulation to complete.
  while (1);

  return 0;
}
