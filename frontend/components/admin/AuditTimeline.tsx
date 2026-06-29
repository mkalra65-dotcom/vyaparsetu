import type { AuditLog } from "@/types/api";

export function AuditTimeline({ logs }: { logs: AuditLog[] }) {
  if (!logs.length) {
    return <p className="text-sm text-slate-600">No audit activity yet.</p>;
  }

  return (
    <div className="grid gap-3">
      {logs.map((log) => (
        <div key={log.id} className="rounded-md border border-slate-200 p-3">
          <p className="text-sm font-semibold text-ink">{log.action.replaceAll("_", " ")}</p>
          <p className="mt-1 text-xs text-slate-500">
            {new Date(log.created_at).toLocaleString("en-IN")} · Actor #{log.actor_user_id}
          </p>
          <p className="mt-2 text-sm text-slate-700">
            {log.old_status || "none"} → {log.new_status || "none"}
          </p>
          {log.note ? <p className="mt-2 text-sm text-slate-600">{log.note}</p> : null}
        </div>
      ))}
    </div>
  );
}
