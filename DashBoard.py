import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  Cell,
} from "recharts";
import {
  TrendingUp,
  Activity,
  BarChart3,
  Download,
  Play,
  Landmark,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import {
  generateBars,
  enrichBars,
  monthlyVolume,
  formatINR,
  formatCompact,
  toCSV,
  type EnrichedBar,
} from "./lib/stockData";
import Candlestick from "./components/Candlestick";

const AXIS_MAROON = "#97144D"; // Axis Bank brand color

function ChartCard({
  title,
  subtitle,
  children,
  right,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-800">{title}</h3>
          {subtitle && <p className="mt-0.5 text-sm text-slate-400">{subtitle}</p>}
        </div>
        {right}
      </div>
      {children}
    </div>
  );
}

function Kpi({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string;
  hint?: React.ReactNode;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded 2xl border p-4 shadow-sm ${
        accent
          ? "border-transparent bg-gradient-to-br from-[#97144D] to-[#c41d63] text-white"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className={`text-xs font-medium uppercase tracking-wide ${accent ? "text-white/70" : "text-slate-400"}`}>
        {label}
      </div>
      <div className={`mt-2 text-2xl font-bold ${accent ? "text-white" : "text-slate-800"}`}>{value}</div>
      {hint && <div className={`mt-1 text-xs ${accent ? "text-white/80" : "text-slate-400"}`}>{hint}</div>}
    </div>
  );
}

export default function App() {
  const [symbol, setSymbol] = useState("AXISBANK.NS");
  const [start, setStart] = useState("2023-01-01");
  const [end, setEnd] = useState(new Date().toISOString().slice(0, 10));
  const [showBollinger, setShowBollinger] = useState(true);
  const [ran, setRan] = useState(true);
  const [nonce, setNonce] = useState(0);

  const bars: EnrichedBar[] = useMemo(() => {
    void nonce;
    const s = new Date(start);
    const e = new Date(end);
    if (isNaN(s.getTime()) || isNaN(e.getTime()) || s >= e) return [];
    const raw = generateBars(symbol, s, e, 950);
    return enrichBars(raw);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ran, nonce]);

  const monthly = useMemo(() => monthlyVolume(bars), [bars]);

  const kpis = useMemo(() => {
    if (bars.length === 0) return null;
    const last = bars[bars.length - 1];
    const prev = bars[bars.length - 2] ?? last;
    const h52 = bars.filter((b) => b.high52w != null);
    const l52 = bars.filter((b) => b.low52w != null);
    const avgHigh = h52.length ? h52.reduce((a, b) => a + (b.high52w ?? 0), 0) / h52.length : last.high;
    const avgLow = l52.length ? l52.reduce((a, b) => a + (b.low52w ?? 0), 0) / l52.length : last.low;
    const totalVol = bars.reduce((a, b) => a + b.volume, 0);
    const dayChange = last.close - prev.close;
    const dayChangePct = (dayChange / prev.close) * 100;
    return {
      lastClose: last.close,
      avgHigh,
      avgLow,
      totalVol,
      rsi: last.rsi ?? 0,
      dayChange,
      dayChangePct,
    };
  }, [bars]);

  const analyze = () => {
    setRan((r) => !r);
  };

  const downloadCSV = () => {
    const blob = new Blob([toCSV(bars)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${symbol}_data.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const priceData = bars.map((b) => ({
    date: b.date,
    Close: b.close,
    "SMA 50": b.sma50,
    "SMA 200": b.sma200,
  }));

  const macdData = bars.filter((b) => b.macd != null).map((b) => ({
    date: b.date,
    MACD: b.macd,
    Signal: b.signal,
    Histogram: b.histogram,
  }));

  const rsiData = bars.filter((b) => b.rsi != null).map((b) => ({ date: b.date, RSI: b.rsi }));

  const tickFormatter = (v: string) => v.slice(0, 7);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Sidebar + main layout */}
      <div className="mx-auto flex max-w-[1400px] flex-col lg:flex-row">
        {/* Sidebar */}
        <aside className="w-full shrink-0 border-b border-slate-200 bg-white p-6 lg:min-h-screen lg:w-72 lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#97144D] text-white shadow-md">
              <Landmark className="h-6 w-6" />
            </div>
            <div>
              <div className="text-sm font-bold leading-tight text-slate-800">Axis Bank</div>
              <div className="text-xs text-slate-400">Stock Analyzer</div>
            </div>
          </div>

          <div className="mt-8 space-y-5">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-500">Stock Symbol</label>
              <input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none focus:border-[#97144D] focus:ring-1 focus:ring-[#97144D]"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-500">Start Date</label>
              <input
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none focus:border-[#97144D] focus:ring-1 focus:ring-[#97144D]"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-500">End Date</label>
              <input
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none focus:border-[#97144D] focus:ring-1 focus:ring-[#97144D]"
              />
            </div>

            <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={showBollinger}
                onChange={(e) => setShowBollinger(e.target.checked)}
                className="h-4 w-4 rounded accent-[#97144D]"
              />
              Show Bollinger Bands
            </label>

            <button
              onClick={analyze}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#97144D] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#7d0f40]"
            >
              <Play className="h-4 w-4" /> Analyze
            </button>

            <button
              onClick={() => setNonce((n) => n + 1)}
              className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
            >
              Regenerate Scenario
            </button>

            <button
              onClick={downloadCSV}
              disabled={bars.length === 0}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
            >
              <Download className="h-4 w-4" /> Download CSV
            </button>
          </div>

          <p className="mt-6 rounded-lg bg-slate-50 p-3 text-[11px] leading-relaxed text-slate-400">
            Data shown is a simulated market scenario for demonstration, computing the same technical
            indicators (SMA, MACD, RSI, Bollinger Bands) used in the original dashboard.
          </p>
        </aside>

        {/* Main */}
        <main className="flex-1 p-6 lg:p-8">
          <header className="mb-6">
            <h1 className="text-2xl font-bold text-slate-800 lg:text-3xl">Axis Bank Stock Dashboard</h1>
            <p className="mt-1 text-sm text-slate-400">
              {symbol} &middot; {start} to {end} &middot; {bars.length} trading days
            </p>
          </header>

          {bars.length === 0 || !kpis ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-400">
              Select a valid date range in the sidebar and click Analyze.
            </div>
          ) : (
            <div className="space-y-6">
              {/* KPI Row */}
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
                <Kpi
                  label="Latest Close"
                  value={formatINR(kpis.lastClose)}
                  accent
                  hint={
                    <span className="inline-flex items-center gap-1">
                      {kpis.dayChange >= 0 ? (
                        <ArrowUpRight className="h-3.5 w-3.5" />
                      ) : (
                        <ArrowDownRight className="h-3.5 w-3.5" />
                      )}
                      {kpis.dayChange >= 0 ? "+" : ""}
                      {kpis.dayChangePct.toFixed(2)}%
                    </span>
                  }
                />
                <Kpi label="Avg 52W High" value={formatINR(kpis.avgHigh)} />
                <Kpi label="Avg 52W Low" value={formatINR(kpis.avgLow)} />
                <Kpi label="Total Volume" value={formatCompact(kpis.totalVol)} hint="shares traded" />
                <Kpi
                  label="Latest RSI"
                  value={kpis.rsi.toFixed(2)}
                  hint={kpis.rsi > 70 ? "Overbought" : kpis.rsi < 30 ? "Oversold" : "Neutral"}
                />
              </div>

              {/* Price + SMA */}
              <ChartCard
                title="Price with Moving Averages"
                subtitle="Close price, SMA 50 and SMA 200"
                right={<TrendingUp className="h-5 w-5 text-slate-300" />}
              >
                <ResponsiveContainer width="100%" height={340}>
                  <LineChart data={priceData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tickFormatter={tickFormatter} minTickGap={40} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                    <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} domain={["auto", "auto"]} />
                    <Tooltip formatter={(v) => (typeof v === "number" ? formatINR(v) : "-")} />
                    <Legend />
                    <Line type="monotone" dataKey="Close" stroke={AXIS_MAROON} strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="SMA 50" stroke="#2563eb" strokeWidth={1.5} dot={false} />
                    <Line type="monotone" dataKey="SMA 200" stroke="#f59e0b" strokeWidth={1.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* Candlestick */}
              <ChartCard
                title="Candlestick with Bollinger Bands"
                subtitle="OHLC price action"
                right={<BarChart3 className="h-5 w-5 text-slate-300" />}
              >
                <Candlestick bars={bars} showBollinger={showBollinger} />
              </ChartCard>

              {/* MACD + RSI grid */}
              <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
                <ChartCard title="MACD Indicator" subtitle="12/26 EMA with 9-period signal">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={macdData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="date" tickFormatter={tickFormatter} minTickGap={40} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                      <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
                      <Tooltip />
                      <Legend />
                      <ReferenceLine y={0} stroke="#cbd5e1" />
                      <Bar dataKey="Histogram" barSize={2}>
                        {macdData.map((d, i) => (
                          <Cell key={i} fill={(d.Histogram ?? 0) >= 0 ? "#16a34a" : "#dc2626"} />
                        ))}
                      </Bar>
                      <Line type="monotone" dataKey="MACD" stroke={AXIS_MAROON} strokeWidth={1.5} dot={false} />
                      <Line type="monotone" dataKey="Signal" stroke="#f59e0b" strokeWidth={1.5} dot={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Relative Strength Index (RSI)" subtitle="14-period, overbought/oversold bands">
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={rsiData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="date" tickFormatter={tickFormatter} minTickGap={40} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                      <Tooltip />
                      <ReferenceLine y={70} stroke="#dc2626" strokeDasharray="4 4" label={{ value: "70", fontSize: 10, fill: "#dc2626" }} />
                      <ReferenceLine y={30} stroke="#16a34a" strokeDasharray="4 4" label={{ value: "30", fontSize: 10, fill: "#16a34a" }} />
                      <Line type="monotone" dataKey="RSI" stroke="#7c3aed" strokeWidth={1.8} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </ChartCard>
              </div>

              {/* Monthly Volume */}
              <ChartCard
                title="Monthly Trading Volume"
                subtitle="Aggregated share volume by month"
                right={<Activity className="h-5 w-5 text-slate-300" />}
              >
                <ResponsiveContainer width="100%" height={340}>
                  <BarChart data={monthly} layout="vertical" margin={{ top: 5, right: 20, left: 30, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis type="number" tickFormatter={formatCompact} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                    <YAxis type="category" dataKey="month" width={80} tick={{ fontSize: 11, fill: "#64748b" }} />
                    <Tooltip formatter={(v) => (typeof v === "number" ? formatCompact(v) : "-")} />
                    <Bar dataKey="volume" fill={AXIS_MAROON} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* Data table */}
              <ChartCard title="Recent Data" subtitle="Last 12 trading days">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
                        <th className="px-3 py-2">Date</th>
                        <th className="px-3 py-2 text-right">Open</th>
                        <th className="px-3 py-2 text-right">High</th>
                        <th className="px-3 py-2 text-right">Low</th>
                        <th className="px-3 py-2 text-right">Close</th>
                        <th className="px-3 py-2 text-right">Change %</th>
                        <th className="px-3 py-2 text-right">RSI</th>
                        <th className="px-3 py-2 text-right">Volume</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bars.slice(-12).reverse().map((b) => (
                        <tr key={b.date} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                          <td className="px-3 py-2 text-slate-600">{b.date}</td>
                          <td className="px-3 py-2 text-right text-slate-600">{b.open.toFixed(2)}</td>
                          <td className="px-3 py-2 text-right text-slate-600">{b.high.toFixed(2)}</td>
                          <td className="px-3 py-2 text-right text-slate-600">{b.low.toFixed(2)}</td>
                          <td className="px-3 py-2 text-right font-medium text-slate-800">{b.close.toFixed(2)}</td>
                          <td className={`px-3 py-2 text-right font-medium ${b.dailyReturnPct >= 0 ? "text-green-600" : "text-red-600"}`}>
                            {b.dailyReturnPct >= 0 ? "+" : ""}
                            {b.dailyReturnPct.toFixed(2)}%
                          </td>
                          <td className="px-3 py-2 text-right text-slate-600">{b.rsi?.toFixed(1) ?? "-"}</td>
                          <td className="px-3 py-2 text-right text-slate-500">{formatCompact(b.volume)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </ChartCard>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
