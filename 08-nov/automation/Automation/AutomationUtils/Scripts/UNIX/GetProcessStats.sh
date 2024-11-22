PROCESS_ID=##Automation--process_id--##

# Getting the process CPU%, thread count and memory using ps and then awk to get the required column
ps_out=$(ps -p $PROCESS_ID -o %cpu,nlwp,rss --no-header)
cpu_usage=$(echo $ps_out | awk '{print $1}')
thread_count=$(echo $ps_out | awk '{print $2}')
memory=$(echo $ps_out | awk '{print $3}')

# Getting the fd/handle count
fd_out=$(ls -l /proc/$PROCESS_ID/fd | wc -l)

# Serializing the result into a comma separated value
echo "handle_count=$fd_out,memory=$memory,thread_count=$thread_count,cpu_usage=$cpu_usage"