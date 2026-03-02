import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <span className="text-xl font-bold">Aftersales</span>
          <div className="flex gap-4">
            <Link href="/login">
              <Button variant="ghost">Anmelden</Button>
            </Link>
            <Link href="/register">
              <Button>Kostenlos starten</Button>
            </Link>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <section className="container flex flex-col items-center justify-center gap-6 py-24 text-center">
          <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl">
            After-Sales Management
          </h1>
          <p className="max-w-[600px] text-lg text-muted-foreground">
            Verwalten Sie Ihren gesamten After-Sales-Prozess an einem Ort.
            Kunden, Projekte, Aufgaben und mehr.
          </p>
          <Link href="/register">
            <Button size="lg">Jetzt starten</Button>
          </Link>
        </section>
      </main>
    </div>
  );
}
