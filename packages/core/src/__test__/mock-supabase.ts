import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * Creates a mock Supabase client for testing tRPC routers.
 * Each query builder method is chainable and returns the builder.
 * Call `mockResult()` to set what `await query` returns.
 */
export function createMockSupabase() {
  let _result: { data: any; error: any } = { data: null, error: null };

  const builder: any = {};
  const chainMethods = [
    "select",
    "insert",
    "update",
    "upsert",
    "delete",
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "is",
    "in",
    "order",
    "limit",
    "range",
    "single",
    "maybeSingle",
  ];

  for (const method of chainMethods) {
    builder[method] = (..._args: any[]) => builder;
  }

  // Make the builder thenable so `await query` resolves to _result
  builder.then = (resolve: any) => resolve(_result);

  const from = (_table: string) => builder;
  const rpc = (_fn: string, _params?: any) =>
    Promise.resolve({ data: null, error: null });

  const supabase = { from, rpc } as unknown as SupabaseClient;

  return {
    supabase,
    /** Set the result that the next query will return */
    mockResult(data: any, error: any = null) {
      _result = { data, error };
    },
    /** Set an error result */
    mockError(message: string) {
      _result = { data: null, error: { message } };
    },
  };
}

/**
 * Creates a mock Supabase with per-table results.
 * Useful when a router procedure calls multiple tables sequentially.
 */
export function createSequentialMockSupabase() {
  const results: { data: any; error: any }[] = [];
  let callIndex = 0;

  const makeBuilder = () => {
    const currentIndex = callIndex++;
    const result = results[currentIndex] ?? { data: null, error: null };

    const builder: any = {};
    const chainMethods = [
      "select",
      "insert",
      "update",
      "upsert",
      "delete",
      "eq",
      "neq",
      "gt",
      "gte",
      "lt",
      "lte",
      "is",
      "in",
      "order",
      "limit",
      "range",
      "single",
      "maybeSingle",
    ];

    for (const method of chainMethods) {
      builder[method] = (..._args: any[]) => builder;
    }

    builder.then = (resolve: any) => resolve(result);
    return builder;
  };

  const from = (_table: string) => makeBuilder();
  const rpc = (_fn: string, _params?: any) =>
    Promise.resolve({ data: null, error: null });
  const supabase = { from, rpc } as unknown as SupabaseClient;

  return {
    supabase,
    /** Push results in the order they'll be consumed */
    pushResult(data: any, error: any = null) {
      results.push({ data, error });
    },
    pushError(message: string) {
      results.push({ data: null, error: { message } });
    },
    /** Reset for next test */
    reset() {
      results.length = 0;
      callIndex = 0;
    },
  };
}
