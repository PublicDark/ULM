#!/usr/bin/env python3
import argparse
import subprocess
import re
import time
import math
import platform
import os
from collections import deque
from threading import Thread
from rich.console import Console
from rich.table import Table
from rich.live import Live


class PingMonitor:
    def __init__(self, target_ip, interval=1):
        self.target_ip = target_ip
        self.interval = interval
        self.samples = deque(maxlen=120)
        self.recent_results = deque(maxlen=120)  
        self.sent = 0
        self.received = 0
        self.running = True
        self.is_windows = platform.system() == "Windows"

    def ping_once(self):
        try:
            # Use Windows-style ping on Windows, Unix-style on Linux/Termux
            if self.is_windows:
                cmd = ['ping', '-n', '1', '-w', '5000', self.target_ip]
                pattern = r'time[=<](\d+)ms'
            else:
                cmd = ['ping', '-c', '1', '-W', '5000', self.target_ip]
                pattern = r'time=(\d+(?:\.\d+)?)'  # Works for both 'time=1.234 ms' and 'time=1.234ms'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.sent += 1
            
            if result.returncode == 0:
                # Search in stdout, fallback to stderr if needed (some systems use stderr for ping output)
                output = result.stdout if result.stdout else result.stderr
                match = re.search(pattern, output)
                if match:
                    latency = float(match.group(1))
                    self.received += 1
                    return latency
            return None
        except Exception as e:
            self.sent += 1
            return None

    def monitor(self):
        while self.running:
            start = time.time()
            latency = self.ping_once()
            elapsed = time.time() - start
            
            if latency is not None:
                self.samples.append(latency)
                self.recent_results.append(True)  
            else:
                self.recent_results.append(False)  
            
            sleep_time = max(0.01, self.interval - elapsed)
            time.sleep(sleep_time)

    def build_table(self):
        table = Table(title=f"| Made By; PublicDark |", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", justify="right", style="yellow")

        if len(self.samples) == 0:
            table.add_row("Status", "[dim]Pinging...[/dim]")
            table.add_row("Packets Sent", str(self.sent))
            return table

        latencies = list(self.samples)
        latest = latencies[-1]
        avg = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        
        if len(self.recent_results) > 0:
            recent_received = sum(self.recent_results)  
            recent_loss = ((len(self.recent_results) - recent_received) / len(self.recent_results) * 100)
        else:
            recent_loss = 0
    
        loss = ((self.sent - self.received) / self.sent * 100) if self.sent > 0 else 0

        if len(self.recent_results) > 0 and not self.recent_results[-1]:
       
            bar = "░" * 40
        else:
      
            if latest < 150:
                color = "green"
            elif latest < 300:
                color = "yellow"
            elif latest < 550:
                color = "orange"
            else:
                color = "red"
            
            max_latency = 4000
            bar_len = int((math.log(latest + 1) / math.log(max_latency + 1)) * 40)
            bar = f"[{color}]{"█" * bar_len}[/{color}]" + "░" * (40 - bar_len)

        table.add_row("Latest", f"{latest:.1f} ms")
        table.add_row("Average", f"{avg:.1f} ms")
        table.add_row("Min", f"{min_lat:.1f} ms")
        table.add_row("Max", f"{max_lat:.1f} ms")
        table.add_row("Sent", str(self.sent))
        table.add_row("Received", str(self.received))
        table.add_row("Loss", f"{loss:.1f}%")
        table.add_row("Bar", bar)

        return table

    def run(self):
      
        console = Console()
        console.clear()
        
    
        monitor_thread = Thread(target=self.monitor, daemon=True)
        monitor_thread.start()

      
        try:
            from rich.live import Live
            with Live(self.build_table(), refresh_per_second=100, console=console) as live:
                while True:
                    live.update(self.build_table())
                    time.sleep(0.01)
        except KeyboardInterrupt:
            self.running = False
            console.print("\n[yellow]Stopped[/yellow]")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor ping latency."
    )
    parser.add_argument("--target", default="1.1.1.1", help="Target IP (default: 1.1.1.1)")
    parser.add_argument("--interval", type=float, default=1, help="Ping interval in seconds (default: 1)")
    args = parser.parse_args()

    monitor = PingMonitor(args.target, args.interval)
    monitor.run()


if __name__ == "__main__":
    main()
