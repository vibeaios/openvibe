import { NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";
import { fixCookieOptions } from "@/lib/supabase/cookies";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/";

  const redirectTo = code ? `${origin}${next}` : `${origin}/login?error=auth`;
  const response = NextResponse.redirect(redirectTo);

  if (code) {
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return request.headers
              .get("cookie")
              ?.split("; ")
              .map((c) => {
                const [name, ...rest] = c.split("=");
                return { name, value: rest.join("=") };
              }) ?? [];
          },
          setAll(
            cookiesToSet: {
              name: string;
              value: string;
              options?: Record<string, unknown>;
            }[]
          ) {
            cookiesToSet.forEach(({ name, value, options }) => {
              response.cookies.set(name, value, fixCookieOptions(options));
            });
          },
        },
      }
    );

    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (error) {
      console.error("[auth/callback] Exchange error:", error.message);
      const errorResponse = NextResponse.redirect(
        `${origin}/login?error=auth`
      );
      return errorResponse;
    }

    // Ensure user record exists
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (user) {
      await supabase.from("users").upsert(
        {
          id: user.id,
          email: user.email!,
          name: user.user_metadata?.full_name ?? user.email?.split("@")[0],
          avatar_url: user.user_metadata?.avatar_url ?? null,
        },
        { onConflict: "id" }
      );
    }
  }

  return response;
}
