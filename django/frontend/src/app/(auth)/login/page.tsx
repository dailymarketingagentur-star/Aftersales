import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>Anmelden</CardTitle>
          <CardDescription>Melden Sie sich bei Ihrem Konto an</CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Noch kein Konto?{" "}
            <Link href="/register" className="underline hover:text-primary">Registrieren</Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
