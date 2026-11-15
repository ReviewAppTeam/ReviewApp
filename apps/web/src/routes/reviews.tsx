import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';
import { useRef, useState } from 'react';

import {
  reviewsImportReviewsMutation,
  reviewsListReviewsOptions,
  reviewsListReviewsQueryKey,
} from '@/api/generated/@tanstack/react-query.gen';

export const Route = createFileRoute('/reviews')({
  component: ReviewsPage,
});

const PAGE_SIZE = 10;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function getImportErrorMessage(error: unknown): string {
  if (!isRecord(error)) {
    return 'Не вдалося імпортувати CSV-файл.';
  }

  const body = isRecord(error.body) ? error.body : undefined;

  const detail =
    typeof error.detail === 'string'
      ? error.detail
      : typeof body?.detail === 'string'
        ? body.detail
        : typeof error.message === 'string'
          ? error.message
          : null;

  const errors = Array.isArray(error.errors)
    ? error.errors
    : Array.isArray(body?.errors)
      ? body.errors
      : [];

  const rowErrors = errors
    .map((item) => {
      if (!isRecord(item) || typeof item.message !== 'string') return null;

      const location =
        typeof item.line === 'number'
          ? `Рядок ${String(item.line)}${
              typeof item.column === 'string' ? `, колонка ${item.column}` : ''
            }: `
          : '';

      return `${location}${item.message}`;
    })
    .filter((item): item is string => item !== null);

  return [detail, ...rowErrors].filter(Boolean).join('\n') || 'Не вдалося імпортувати CSV-файл.';
}

function ReviewsPage() {
  const [page, setPage] = useState(1);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const reviewsQuery = useQuery(
    reviewsListReviewsOptions({
      query: {
        page,
        page_size: PAGE_SIZE,
      },
    }),
  );

  const importMutation = useMutation({
    ...reviewsImportReviewsMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: reviewsListReviewsQueryKey(),
      });
    },
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      window.alert('Будь ласка, виберіть CSV-файл.');
      event.target.value = '';
      return;
    }

    importMutation.mutate({
      body: {
        file,
      },
    });

    event.target.value = '';
  };

  const reviews = reviewsQuery.data?.items ?? [];
  const total = reviewsQuery.data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 p-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Відгуки</h1>
          <p className="mt-1 text-sm text-gray-500">Перегляд та імпорт відгуків із CSV-файлів</p>
        </div>

        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={handleFileChange}
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={importMutation.isPending}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {importMutation.isPending ? 'Імпорт триває...' : 'Імпортувати CSV'}
          </button>
        </div>
      </header>

      {importMutation.isSuccess && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          Імпорт завершено. Отримано: {importMutation.data.received}, імпортовано:{' '}
          {importMutation.data.imported}, пропущено дублікатів:{' '}
          {importMutation.data.skipped_duplicates}.
        </div>
      )}

      {importMutation.isError && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm whitespace-pre-line text-red-800"
        >
          {getImportErrorMessage(importMutation.error)}
        </div>
      )}

      {reviewsQuery.isError && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800"
        >
          Не вдалося завантажити відгуки.
          <button
            type="button"
            onClick={() => {
              void reviewsQuery.refetch();
            }}
            className="ml-2 underline"
          >
            Спробувати ще раз
          </button>
        </div>
      )}

      {reviewsQuery.isPending ? (
        <div className="py-12 text-center text-gray-500">Завантаження відгуків...</div>
      ) : reviewsQuery.isError ? null : reviews.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 px-6 py-16 text-center">
          <h2 className="text-lg font-medium">Відгуків поки немає</h2>
          <p className="mt-2 text-sm text-gray-500">Імпортуйте CSV-файл, щоб додати відгуки.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200">
            <table className="w-full border-collapse text-left text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Дата</th>
                  <th className="px-4 py-3 font-medium">Джерело</th>
                  <th className="px-4 py-3 font-medium">Оцінка</th>
                  <th className="px-4 py-3 font-medium">Текст</th>
                </tr>
              </thead>

              <tbody>
                {reviews.map((review) => (
                  <tr key={review.id} className="border-t border-gray-200">
                    <td className="px-4 py-3 whitespace-nowrap">
                      {new Date(review.reviewed_at).toLocaleDateString('uk-UA')}
                    </td>
                    <td className="px-4 py-3">{review.source}</td>
                    <td className="px-4 py-3 whitespace-nowrap">{review.rating} / 5</td>
                    <td className="min-w-64 px-4 py-3">
                      <p className="max-w-xl whitespace-pre-wrap">{review.text}</p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="text-sm text-gray-500">Усього відгуків: {total}</p>

            <div className="flex items-center gap-3">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => {
                  setPage((current) => current - 1);
                }}
                className="rounded-lg border px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40"
              >
                Попередня
              </button>

              <span className="text-sm text-gray-600">
                Сторінка {page} із {totalPages}
              </span>

              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => {
                  setPage((current) => current + 1);
                }}
                className="rounded-lg border px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40"
              >
                Наступна
              </button>
            </div>
          </div>
        </>
      )}
    </main>
  );
}
