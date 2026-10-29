import TradingLab from "@/components/TradingLab";

export default function Home() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-2xl font-semibold">STDevsec Trading Lab</h1>
      <p className="mt-2 text-sm text-neutral-500">
        Investigación cuantitativa y educación de trading. Solo simulación — esto
        no es asesoría financiera ni representa desempeño real de mercado.
      </p>

      <section className="mt-8">
        <TradingLab />
      </section>
    </main>
  );
}
