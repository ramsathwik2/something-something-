import psutil
import time
import threading

class ActivityMonitor:
    def __init__(self, cpu_thresh=42.0):
        self.cpu_thresh = cpu_thresh
        self.last_process_count = len(psutil.pids())
        self._callback = None
        self._running = False
        self._thread = None

    def start(self, callback):
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        # debounce: need 2 consecutive hits before alert
        consec=0
        cooldown_until=0
        while self._running:
            try:
                cpu = psutil.cpu_percent(interval=1.2)
                pcount = len(psutil.pids())
                new_proc = pcount != self.last_process_count
                self.last_process_count = pcount
                import time as _t
                now=_t.time()
                activity=False; reason=""
                if now < cooldown_until:
                    activity=False
                elif cpu > self.cpu_thresh:
                    consec+=1
                    if consec>=2:
                        activity=True; reason=f"CPU {cpu:.0f}%"
                        cooldown_until=now+8
                        consec=0
                    else:
                        activity=False # need second hit
                elif new_proc and cpu > 18:
                    consec+=1
                    if consec>=2:
                        activity=True; reason="new process"
                        cooldown_until=now+8
                        consec=0
                else:
                    consec = max(0, consec-1)
                if self._callback:
                    self._callback(activity, reason, cpu, pcount)
            except Exception as e:
                print("monitor error", e)
            time.sleep(1.4)
