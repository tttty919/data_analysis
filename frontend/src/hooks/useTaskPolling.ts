"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { getTaskProgress } from "@/lib/api";
import { TaskProgress } from "@/lib/types";
import { POLLING_INTERVAL, MAX_POLL_TIME } from "@/lib/constants";

export function useTaskPolling(taskId: string | null, enabled: boolean) {
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!taskId || !enabled) {
      stopPolling();
      return;
    }

    startTimeRef.current = Date.now();
    setIsComplete(false);

    const poll = async () => {
      try {
        const p = await getTaskProgress(taskId);
        setProgress(p);

        if (["completed", "failed", "stopped"].includes(p.phase)) {
          setIsComplete(true);
          stopPolling();
          return;
        }

        if (Date.now() - startTimeRef.current > MAX_POLL_TIME) {
          setIsComplete(true);
          stopPolling();
        }
      } catch {
        // ignore polling errors
      }
    };

    poll();
    intervalRef.current = setInterval(poll, POLLING_INTERVAL);

    return () => stopPolling();
  }, [taskId, enabled, stopPolling]);

  return { progress, isComplete, stopPolling };
}
