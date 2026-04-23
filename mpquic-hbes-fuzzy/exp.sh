#!/bin/bash
./quic_mptcp_https_tests_expdes_wsp_lowbdp_quic.py && python3 findfilecompeletetime.py && python3 line_processing.py && python reTestFailedEXP
# && python calculateofo.py
