package net.activeinference.beacon.core;
import neural.studio.*;


import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import java.util.ArrayList;
import java.util.List;

public class SystemBusKernel {
    public static List<String> inspectActiveJavaThreads() {
        List<String> threadLogs = new ArrayList<>();
        ThreadMXBean bean = ManagementFactory.getThreadMXBean();
        long[] ids = bean.getAllThreadIds();
        ThreadInfo[] infos = bean.getThreadInfo(ids);
        
        threadLogs.add(String.format("[🚌 JVM BUS] Intercepted %d active threads running inside container...", ids.length));
        for (ThreadInfo info : infos) {
            if (info != null) {
                threadLogs.add(String.format(" |── ID: %d | Name: %s | State: %s", 
                    info.getThreadId(), info.getThreadName(), info.getThreadState()));
            }
        }
        return threadLogs;
    }
}
