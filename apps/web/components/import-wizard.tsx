'use client';

import { Upload, X } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

import { createImportJob, getImportJob, listContactLists } from '@/lib/api';
import type { ContactList, ImportJob } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

type Step = 1 | 2 | 3 | 'progress';

const CANONICAL_FIELDS = ['email', 'first_name', 'last_name', 'ignore'] as const;

// ---------------------------------------------------------------------------
// Progress display
// ---------------------------------------------------------------------------

function ImportProgress({
  job,
  onClose,
}: {
  job: ImportJob;
  onClose: () => void;
}) {
  const pct =
    job.total_rows > 0
      ? Math.round((job.processed_rows / job.total_rows) * 100)
      : job.status === 'completed'
      ? 100
      : 0;

  const statusColour: Record<ImportJob['status'], string> = {
    pending: 'text-[var(--muted)]',
    processing: 'text-blue-500',
    completed: 'text-green-600',
    failed: 'text-red-500',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Import Progress</h3>
        {(job.status === 'completed' || job.status === 'failed') && (
          <button onClick={onClose} aria-label="Close"><X className="size-5" /></button>
        )}
      </div>

      <p className={`text-sm font-medium capitalize ${statusColour[job.status]}`}>
        {job.status}
      </p>

      {/* Progress bar */}
      <div className="h-3 w-full rounded-full bg-[var(--card-border)] overflow-hidden">
        <div
          className="h-full rounded-full bg-[var(--primary)] transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="grid grid-cols-4 gap-3 text-center text-sm">
        {[
          { label: 'Processed', value: job.processed_rows },
          { label: 'Imported', value: job.imported_count },
          { label: 'Skipped', value: job.skipped_count },
          { label: 'Errors', value: job.error_count },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-xl bg-[var(--surface)] border border-[var(--card-border)] p-3">
            <p className="text-xl font-bold">{value}</p>
            <p className="text-xs text-[var(--muted)] mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Error report */}
      {job.error_report && job.error_report.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-red-500">Error Report ({job.error_report.length})</p>
          <div className="max-h-48 overflow-y-auto rounded-xl border border-[var(--card-border)]">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b border-[var(--card-border)]">
                  <th className="px-3 py-2 text-left text-[var(--muted)] font-medium">Row</th>
                  <th className="px-3 py-2 text-left text-[var(--muted)] font-medium">Error</th>
                </tr>
              </thead>
              <tbody>
                {job.error_report.map((e, i) => (
                  <tr key={i} className="border-b border-[var(--card-border)] last:border-0">
                    <td className="px-3 py-2">{e.row}</td>
                    <td className="px-3 py-2 text-red-500">{e.error}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Import Wizard
// ---------------------------------------------------------------------------

export function ImportWizard({ onClose, onDone }: { onClose: () => void; onDone?: () => void }) {
  const [step, setStep] = useState<Step>(1);
  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [lists, setLists] = useState<ContactList[]>([]);
  const [selectedListId, setSelectedListId] = useState<string>('');
  const [job, setJob] = useState<ImportJob | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    listContactLists().then(setLists).catch(() => {});
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // Parse CSV headers from the first line
  const parseHeaders = (f: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const firstLine = text.split('\n')[0] ?? '';
      const cols = firstLine.split(',').map((h) => h.trim().replace(/^"|"$/g, ''));
      setHeaders(cols);
      // Default mapping: if column header matches canonical name, pre-select it
      const defaultMap: Record<string, string> = {};
      for (const col of cols) {
        const lower = col.toLowerCase().replace(/\s+/g, '_');
        if (lower === 'email' || lower === 'first_name' || lower === 'last_name') {
          defaultMap[col] = lower;
        } else {
          defaultMap[col] = col; // pass-through as custom field
        }
      }
      setMapping(defaultMap);
    };
    reader.readAsText(f);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    parseHeaders(f);
  };

  const startPolling = useCallback((jobId: number) => {
    pollRef.current = setInterval(async () => {
      try {
        const updated = await getImportJob(jobId);
        setJob(updated);
        if (updated.status === 'completed' || updated.status === 'failed') {
          if (pollRef.current) clearInterval(pollRef.current);
          if (updated.status === 'completed') onDone?.();
        }
      } catch {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    }, 1500);
  }, [onDone]);

  const handleSubmit = async () => {
    if (!file) return;
    // Build canonical mapping (only include non-ignore cols)
    const canonicalMap: Record<string, string> = {};
    for (const [col, target] of Object.entries(mapping)) {
      if (target && target !== 'ignore') {
        canonicalMap[target] = col;
      }
    }

    try {
      const created = await createImportJob(file, {
        contactListId: selectedListId ? Number(selectedListId) : undefined,
        columnMapping: Object.keys(canonicalMap).length > 0 ? canonicalMap : undefined,
      });
      setJob(created);
      setStep('progress');
      startPolling(created.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to start import');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-lg p-6 space-y-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {step === 'progress' ? 'Importing…' : `Import Contacts — Step ${step} of 3`}
          </h2>
          <button onClick={onClose} aria-label="Close"><X className="size-5" /></button>
        </div>

        {/* Step 1: File Upload */}
        {step === 1 && (
          <div className="space-y-4">
            <p className="text-sm text-[var(--muted)]">
              Upload a CSV file. The first row must be headers.
              Maximum 50,000 rows / 10 MB.
            </p>
            <div
              className="rounded-2xl border-2 border-dashed border-[var(--card-border)] p-10 text-center cursor-pointer hover:border-[var(--primary)] transition-colors"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="mx-auto size-8 text-[var(--muted)] mb-2" />
              {file ? (
                <p className="text-sm font-medium">{file.name}</p>
              ) : (
                <p className="text-sm text-[var(--muted)]">Click to select a CSV file</p>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
            <div className="flex justify-end">
              <Button disabled={!file} onClick={() => setStep(2)}>Next →</Button>
            </div>
          </div>
        )}

        {/* Step 2: Column Mapping */}
        {step === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-[var(--muted)]">
              Map each CSV column to a contact field. Columns mapped to{' '}
              <code className="text-xs">ignore</code> will be skipped. Anything not mapped
              to a known field becomes a custom field.
            </p>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {headers.map((col) => (
                <div key={col} className="flex items-center gap-3">
                  <span className="flex-1 text-sm font-mono truncate" title={col}>{col}</span>
                  <select
                    value={mapping[col] ?? ''}
                    onChange={(e) => setMapping((m) => ({ ...m, [col]: e.target.value }))}
                    className="w-44 rounded-md border border-[var(--card-border)] bg-[var(--surface)] px-2 py-1 text-sm"
                  >
                    <option value={col}>{col} (custom field)</option>
                    <option value="email">email</option>
                    <option value="first_name">first_name</option>
                    <option value="last_name">last_name</option>
                    <option value="ignore">ignore</option>
                  </select>
                </div>
              ))}
            </div>
            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>← Back</Button>
              <Button onClick={() => setStep(3)}>Next →</Button>
            </div>
          </div>
        )}

        {/* Step 3: Confirm */}
        {step === 3 && (
          <div className="space-y-4">
            <div className="rounded-xl border border-[var(--card-border)] p-4 text-sm space-y-1">
              <p><span className="text-[var(--muted)]">File:</span> {file?.name}</p>
              <p>
                <span className="text-[var(--muted)]">Email column:</span>{' '}
                {Object.entries(mapping).find(([, v]) => v === 'email')?.[0] ?? '(auto-detect)'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Add to Contact List (optional)</label>
              <select
                value={selectedListId}
                onChange={(e) => setSelectedListId(e.target.value)}
                className="mt-1 w-full rounded-md border border-[var(--card-border)] bg-[var(--surface)] px-3 py-2 text-sm"
              >
                <option value="">None</option>
                {lists.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </div>
            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(2)}>← Back</Button>
              <Button onClick={() => void handleSubmit()}>Start Import</Button>
            </div>
          </div>
        )}

        {/* Progress */}
        {step === 'progress' && job && (
          <ImportProgress
            job={job}
            onClose={() => { onClose(); onDone?.(); }}
          />
        )}
      </Card>
    </div>
  );
}
