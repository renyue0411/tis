bandwidth = '5'
delay = '5'

mptcpTopos_custom = []

for _ in range(30):

    topology = {
        'paths': [{'queuingDelay': '0.048', 'bandwidth': bandwidth, 'delay': delay, 'jitter': '0'},
                  {'queuingDelay': '0.048', 'bandwidth': '5', 'delay': '5', 'jitter': '0'}],
        'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]
    }
    mptcpTopos_custom.append(topology)

print(mptcpTopos_custom)

# i = 0
# for topos in mptcpTopos_custom:
#     print(mptcpTopos_custom[i]['paths'])
#     print("\n")
#     i = i + 1
