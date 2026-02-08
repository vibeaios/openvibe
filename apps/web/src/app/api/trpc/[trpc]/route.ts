import { fetchRequestHandler } from "@trpc/server/adapters/fetch";
import { appRouter, type Context } from "@openvibe/core";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { fixCookieOptions } from "@/lib/supabase/cookies";

const handler = async (req: Request) => {
  return fetchRequestHandler({
    endpoint: "/api/trpc",
    req,
    router: appRouter,
    createContext: async (): Promise<Context> => {
      const cookieStore = await cookies();

      const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
          cookies: {
            getAll() {
              return cookieStore.getAll();
            },
            setAll(
              cookiesToSet: {
                name: string;
                value: string;
                options?: Record<string, unknown>;
              }[]
            ) {
              try {
                cookiesToSet.forEach(({ name, value, options }) =>
                  cookieStore.set(name, value, fixCookieOptions(options))
                );
              } catch {
                // Route handler context — ignore
              }
            },
          },
        }
      );

      const {
        data: { user },
      } = await supabase.auth.getUser();

      const allCookies = cookieStore.getAll();
      console.log("[tRPC] cookies:", allCookies.map(c => c.name));
      console.log("[tRPC] userId:", user?.id ?? "null", "email:", user?.email ?? "null");

      return {
        userId: user?.id ?? null,
        supabase,
      };
    },
  });
};

export { handler as GET, handler as POST };
