// Copyright 2022 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

#include <svdpi.h>

#include <string>
#include <vector>
#include <map>
#include <iostream>
#include <fstream>
#include <sstream>
#include <stdint.h>

// main dimension: taint id.
// address and length.
std::vector<std::vector<std::pair<uint64_t, uint64_t>>> taint_sections;
// main dimension: taint id.
// address and taint assignment hex.
std::vector<std::map<uint64_t, std::string>> taint_assignments;

static std::vector<int> taint_section_index;

extern "C" {
  void init_taint_vectors(long long num_taints);
  char read_taint_section(long long taint_id, long long address, const svOpenArrayHandle buffer);
  void read_taints(const char* filename);
}

extern "C" void init_taint_vectors(long long num_taints) {
  taint_sections.resize(num_taints);
  taint_assignments.resize(num_taints);
  taint_section_index.resize(num_taints, 0);
}

// Communicate the section address and len
// Returns:
// 0 if there are no more sections
// 1 if there are more sections to load
extern "C" char get_taint_section(long long taint_id, long long* address, long long* len) {
  if (taint_section_index[taint_id] < taint_sections[taint_id].size()) {
    *address = taint_sections[taint_id][taint_section_index[taint_id]].first;
    *len = taint_sections[taint_id][taint_section_index[taint_id]].second;
    taint_section_index[taint_id]++;
    return 1;
  } else {
    return 0;
  }
}

static inline char char_to_hex(char c) {
  if (c >= '0' && c <= '9')
    return c-'0';
  else if (c >= 'a' && c <= 'f')
    return c-'a'+10;
  else if (c >= 'A' && c <= 'F')
    return c-'A'+10;

  std::cerr << "Error in taint assignment string. Unexpected character: " << c << std::endl;
  exit(0);
}

extern "C" char read_taint_section(long long taint_id, long long address, const svOpenArrayHandle buffer) {
  // get actual poitner
  void* buf = svGetArrayPtr(buffer);
  // interpret the taint assignment string.
  std::string taint_assignment_str = taint_assignments[taint_id][address];
  size_t num_bytes = taint_assignment_str.size() / 2;

  for (int byte_offset = 0; byte_offset < num_bytes; byte_offset++) {
    char byte_val = (char_to_hex(taint_assignment_str[2*byte_offset]) << 4) | char_to_hex(taint_assignment_str[2*byte_offset+1]); 
    *((char *) buf + byte_offset) = byte_val;
  }
  return 0;
}

extern "C" void read_taints(const char* filename) {
  std::ifstream f;
  f.open(filename);

  uint64_t taint_id;
  std::string region_offset_str;
  uint64_t num_bytes;
  std::string byte_taint_contents;

  uint64_t region_offset;
  std::string tmp_line;
  while (std::getline(f, tmp_line)) {
    if (!tmp_line.size())
        continue;
    std::istringstream isstream(tmp_line);
    isstream >> taint_id;
    isstream >> region_offset_str;
    isstream >> num_bytes;
    isstream >> byte_taint_contents;

    std::istringstream str_to_hex_stream(region_offset_str);
    str_to_hex_stream >> std::hex >> region_offset;

    taint_sections[taint_id].push_back(std::make_pair(region_offset, num_bytes));
    taint_assignments[taint_id][region_offset] = byte_taint_contents;
  }

  f.close();
}
