"use client";

import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const handleGoogleLogin = async () => {
    const supabase = createClient();
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  };

  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 text-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">OpenVibe</h1>
          <p className="mt-2 text-muted-foreground">
            AI-native team collaboration
          </p>
        </div>

        <button
          onClick={handleGoogleLogin}
          className="w-full rounded-lg bg-foreground px-4 py-3 text-sm font-medium text-background transition-colors hover:opacity-90"
        >
          Continue with Google
        </button>
      </div>
    </div>
  );
}
