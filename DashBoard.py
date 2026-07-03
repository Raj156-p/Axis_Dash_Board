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

// # Brand & Style Constants ─────────────────────────────────────────────────

const AXIS_BRAND_COLOR = "#97144D"; // Axis Bank's signature maroon
const AXIS_BRAND_HOVER = "#7d0f40"; // Darker shade for hover states

const CHART_COLORS = {
  close: AXIS_BRAND_COLOR,
  sma50: "#2563eb", // Blue
  sma200: "#f59e0b", // Amber
  rsi: "#7c3aed", // Purple
  macdSignal: "#f59e0b", // Amber
  bullish: "#16a34a", // Green
  bearish: "#dc2626", // Red
  gridLine: "#f1f5f9", // Very light gray
  axisText: "#94a3b8", // Muted gray
  refLine: "#cbd5e1", // Light border gray
};

// ─── Reusable UI Components ──────────────────────────────────────────────────

/**
 * A card wrapper used for each chart/section.
 * Provides a consistent look with a title, optional subtitle, and an optional
 * icon or action on the right side.
 */
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
      {/* Header row: title on the left, optional icon/action on the right */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-800">{title}</h3>
          {subtitle && (
            <p className="mt-0.5 text-sm text-slate-400">{subtitle}</p>
          )}
        </div>
        {right}
      </div>

      {children}
    </div>
  );
}

/**
 * A single KPI (Key Performance Indicator) tile.
 * When `accent` is true, it uses the Axis Bank brand gradient background
 * to visually highlight the most important metric.
 */
function KpiTile({
  label,
  value,
  hint,
  isAccented = false,
}: {
  label: string;
  value: string;
  hint?: React.ReactNode;
  isAccented?: boolean;
}) {
  // Pick text/background styles based on whether this tile is accented
  const wrapperStyle = isAccented
    ? "border-transparent bg-gradient-to-br from-[#97144D] to-[#c41d63] text-white"
    : "border-slate-200 bg-white";

  const labelStyle = isAccented ? "text-white/70" : "text-slate-400";
  const valueStyle = isAccented ? "text-white" : "text-slate-800";
  const hintStyle = isAccented ? "text-white/80" : "text-slate-400";

  return (
    <div className={`rounded-2xl border p-4 shadow-sm ${wrapperStyle}`}>
      <div className={`text-xs font-medium uppercase tracking-wide ${labelStyle}`}>
        {label}
      </div>
      <div className={`mt-2 text-2xl font-bold ${valueStyle}`}>
        {value}
      </div>
      {hint && (
        <div className={`mt-1 text-xs ${hintStyle}`}>{hint}</div>
      )}
    </div>
  );
}

// ─── Helper Functions ────────────────────────────────────────────────────────

/** Shorten a date string like "2024-03-15" down to "2024-03" for chart ticks. */
function shortenDate(dateString: string): string {
  return dateString.slice(0, 7);
}

/**
 * Determine a human-readable RSI status label.
 *  - Above 70 → Overbought (price may be due for a pullback)
 *  - Below 30 → Oversold   (price may be due for a bounce)
 *  - Otherwise → Neutral
 */
function describeRsi(rsiValue: number): string {
  if (rsiValue > 70) return "Overbought";
  if (rsiValue < 30) return "Oversold";
  return "Neutral";
}

/**
 * Compute summary statistics from the enriched bar data.
 * Returns null if there's no data to work with.
 */
function computeKpis(bars: EnrichedBar[]) {
  if (bars.length === 0) return null;

  const lastBar = bars[bars.length - 1];
  const previousBar = bars.length >= 2 ? bars[bars.length - 2] : lastBar;

  // Calculate average 52-week high from all bars that have the value
  const barsWithHigh52 = bars.filter((bar) => bar.high52w != null);
  const averageHigh52w = barsWithHigh52.length > 0
    ? barsWithHigh52.reduce((sum, bar) => sum + (bar.high52w ?? 0), 0) / barsWithHigh52.length
    : lastBar.high;

  // Calculate average 52-week low similarly
  const barsWithLow52 = bars.filter((bar) => bar.low52w != null);
  const averageLow52w = barsWithLow52.length > 0
    ? barsWithLow52.reduce((sum, bar) => sum + (bar.low52w ?? 0), 0) / barsWithLow52.length
    : lastBar.low;

  // Sum up the total trading volume across all bars
  const totalVolume = bars.reduce((sum, bar) => sum + bar.volume, 0);

  // Day-over-day price change
  const dailyPriceChange = lastBar.close - previousBar.close;
  const dailyPriceChangePercent = (dailyPriceChange / previousBar.close) * 100;

  return {
    lastClose: lastBar.close,
    averageHigh52w,
    averageLow52w,
    totalVolume,
    latestRsi: lastBar.rsi ?? 0,
    dailyPriceChange,
    dailyPriceChangePercent,
  };
}

// ─── Chart Data Transformers ─────────────────────────────────────────────────

/** Reshape bars into the format the price + SMA line chart expects. */
function buildPriceChartData(bars: EnrichedBar[]) {
  return bars.map((bar) => ({
    date: bar.date,
    Close: bar.close,
    "SMA 50": bar.sma50,
    "SMA 200": bar.sma200,
  }));
}

/** Reshape bars into MACD chart data, excluding bars where MACD hasn't warmed up yet. */
function buildMacdChartData(bars: EnrichedBar[]) {
  return bars
    .filter((bar) => bar.macd != null)
    .map((bar) => ({
      date: bar.date,
      MACD: bar.macd,
      Signal: bar.signal,
      Histogram: bar.histogram,
    }));
}

/** Reshape bars into RSI chart data, excluding bars where RSI hasn't warmed up yet. */
function buildRsiChartData(bars: EnrichedBar[]) {
  return bars
    .filter((bar) => bar.rsi != null)
    .map((bar) => ({
      date: bar.date,
      RSI: bar.rsi,
    }));
}

// ─── Main Application Component ─────────────────────────────────────────────

export default function App() {
  // ── User Inputs ──────────────────────────────────────────────────────────

  const [symbol, setSymbol] = useState("AXISBANK.NS");
  const [startDate, setStartDate] = useState("2023-01-01");
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [showBollingerBands, setShowBollingerBands] = useState(true);

  // These two pieces of state act as "triggers" to force data regeneration:
  //  - `analysisToggle` flips when the user clicks "Analyze"
  //  - `scenarioCounter` increments when the user clicks "Regenerate Scenario"
  const [analysisToggle, setAnalysisToggle] = useState(true);
  const [scenarioCounter, setScenarioCounter] = useState(0);

  // ── Derived Data (memoized for performance) ──────────────────────────────

  // Generate and enrich the simulated stock bars whenever analysis is triggered
  const enrichedBars: EnrichedBar[] = useMemo(() => {
    // Reference scenarioCounter so changes to it trigger recalculation
    void scenarioCounter;

    const parsedStart = new Date(startDate);
    const parsedEnd = new Date(endDate);

    // Bail out with empty data if the date range is invalid
    const isInvalidRange =
      isNaN(parsedStart.getTime()) ||
      isNaN(parsedEnd.getTime()) ||
      parsedStart >= parsedEnd;

    if (isInvalidRange) return [];

    const rawBars = generateBars(symbol, parsedStart, parsedEnd, 950);
    return enrichBars(rawBars);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysisToggle, scenarioCounter]);

  // Aggregate volume by month for the horizontal bar chart
  const monthlyVolumeData = useMemo(
    () => monthlyVolume(enrichedBars),
    [enrichedBars]
  );

  // Compute headline KPI numbers from the bar data
  const kpis = useMemo(
    () => computeKpis(enrichedBars),
    [enrichedBars]
  );

  // Prepare chart-specific data shapes
  const priceChartData = buildPriceChartData(enrichedBars);
  const macdChartData = buildMacdChartData(enrichedBars);
  const rsiChartData = buildRsiChartData(enrichedBars);

  // ── User Actions ─────────────────────────────────────────────────────────

  /** Trigger a new analysis with the current symbol and date range. */
  function handleAnalyze() {
    setAnalysisToggle((previous) => !previous);
  }

  /** Regenerate the random scenario data while keeping the same inputs. */
  function handleRegenerateScenario() {
    setScenarioCounter((count) => count + 1);
  }

  /** Download the current bar data as a CSV file. */
  function handleDownloadCsv() {
    const csvContent = toCSV(enrichedBars);
    const blob = new Blob([csvContent], { type: "text/csv" });
    const downloadUrl = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `${symbol}_data.csv`;
    link.click();

    URL.revokeObjectURL(downloadUrl);
  }

  // ── Shared Chart Props ───────────────────────────────────────────────────

  const commonAxisProps = { fontSize: 11, fill: CHART_COLORS.axisText };

  // ── Render ───────────────────────────────────────────────────────────────

  const hasData = enrichedBars.length > 0 && kpis !== null;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-[1400px] flex-col lg:flex-row">

        {/* ════════════════════════════════════════════════════════════════
            SIDEBAR — inputs, controls, and branding
            ════════════════════════════════════════════════════════════════ */}
        <aside className="w-full shrink-0 border-b border-slate-200 bg-white p-6 lg:min-h-screen lg:w-72 lg:border-b-0 lg:border-r">

          {/* Brand logo and name */}
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#97144D] text-white shadow-md">
              <Landmark className="h-6 w-6" />
            </div>
            <div>
              <div className="text-sm font-bold leading-tight text-slate-800">
                Axis Bank
              </div>
              <div className="text-xs text-slate-400">Stock Analyzer</div>
            </div>
          </div>

          {/* Input controls */}
          <div className="mt-8 space-y-5">

            {/* Stock symbol */}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-500">
                Stock Symbol
              </label>
              <input
                value={symbol}
                onChange={(event) => setSymbol(event.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none focus:border-[#97144D] focus:ring-1 focus:ring-[#97144D]"
              />
            </div>

            {/* Start date picker */}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-500">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none focus:border-[#97144D] focus:ring-1 focus:ring-[#97144D]"
              />
            </div>

            {/* End date picker */}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-500">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(event) => setEndDate(event.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none focus:border-[#97144D] focus:ring-1 focus:ring-[#97144D]"
              />
            </div>

            {/* Bollinger Bands toggle */}
            <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={showBollingerBands}
                onChange={(event) => setShowBollingerBands(event.target.checked)}
                className="h-4 w-4 rounded accent-[#97144D]"
              />
              Show Bollinger Bands
            </label>

            {/* Primary action: run analysis */}
            <button
              onClick={handleAnalyze}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#97144D] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#7d0f40]"
            >
              <Play className="h-4 w-4" /> Analyze
            </button>

            {/* Secondary action: new random data with same inputs */}
            <button
              onClick={handleRegenerateScenario}
              className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
            >
              Regenerate Scenario
            </button>

            {/* CSV export */}
            <button
              onClick={handleDownloadCsv}
              disabled={enrichedBars.length === 0}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
            >
              <Download className="h-4 w-4" /> Download CSV
            </button>
          </div>

          {/* Disclaimer */}
          <p className="mt-6 rounded-lg bg-slate-50 p-3 text-[11px] leading-relaxed text-slate-400">
            Data shown is a simulated market scenario for demonstration,
            computing the same technical indicators (SMA, MACD, RSI, Bollinger
            Bands) used in the original dashboard.
          </p>
        </aside>

        {/* ════════════════════════════════════════════════════════════════
            MAIN CONTENT — charts, KPIs, and data table
            ════════════════════════════════════════════════════════════════ */}
        <main className="flex-1 p-6 lg:p-8">

          {/* Page heading */}
          <header className="mb-6">
            <h1 className="text-2xl font-bold text-slate-800 lg:text-3xl">
              Axis Bank Stock Dashboard
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              {symbol} &middot; {startDate} to {endDate} &middot;{" "}
              {enrichedBars.length} trading days
            </p>
          </header>

          {/* Show a placeholder if we have no data yet */}
          {!hasData ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-400">
              Select a valid date range in the sidebar and click Analyze.
            </div>
          ) : (
            <div className="space-y-6">

              {/* ── KPI Summary Row ─────────────────────────────────────── */}
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
                <KpiTile
                  label="Latest Close"
                  value={formatINR(kpis.lastClose)}
                  isAccented
                  hint={
                    <span className="inline-flex items-center gap-1">
                      {kpis.dailyPriceChange >= 0 ? (
                        <ArrowUpRight className="h-3.5 w-3.5" />
                      ) : (
                        <ArrowDownRight className="h-3.5 w-3.5" />
                      )}
                      {kpis.dailyPriceChange >= 0 ? "+" : ""}
                      {kpis.dailyPriceChangePercent.toFixed(2)}%
                    </span>
                  }
                />
                <KpiTile
                  label="Avg 52W High"
                  value={formatINR(kpis.averageHigh52w)}
                />
                <KpiTile
                  label="Avg 52W Low"
                  value={formatINR(kpis.averageLow52w)}
                />
                <KpiTile
                  label="Total Volume"
                  value={formatCompact(kpis.totalVolume)}
                  hint="shares traded"
                />
                <KpiTile
                  label="Latest RSI"
                  value={kpis.latestRsi.toFixed(2)}
                  hint={describeRsi(kpis.latestRsi)}
                />
              </div>

              {/* ── Price with Moving Averages (Line Chart) ─────────────── */}
              <ChartCard
                title="Price with Moving Averages"
                subtitle="Close price, SMA 50 and SMA 200"
                right={<TrendingUp className="h-5 w-5 text-slate-300" />}
              >
                <ResponsiveContainer width="100%" height={340}>
                  <LineChart
                    data={priceChartData}
                    margin={{ top: 5, right: 10, left: -10, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.gridLine} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={shortenDate}
                      minTickGap={40}
                      tick={commonAxisProps}
                    />
                    <YAxis tick={commonAxisProps} domain={["auto", "auto"]} />
                    <Tooltip
                      formatter={(value) =>
                        typeof value === "number" ? formatINR(value) : "-"
                      }
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="Close"
                      stroke={CHART_COLORS.close}
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="SMA 50"
                      stroke={CHART_COLORS.sma50}
                      strokeWidth={1.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="SMA 200"
                      stroke={CHART_COLORS.sma200}
                      strokeWidth={1.5}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* ── Candlestick Chart with Bollinger Bands ───────────────── */}
              <ChartCard
                title="Candlestick with Bollinger Bands"
                subtitle="OHLC price action"
                right={<BarChart3 className="h-5 w-5 text-slate-300" />}
              >
                <Candlestick
                  bars={enrichedBars}
                  showBollinger={showBollingerBands}
                />
              </ChartCard>

              {/* ── MACD & RSI Side-by-Side ──────────────────────────────── */}
              <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">

                {/* MACD Indicator */}
                <ChartCard
                  title="MACD Indicator"
                  subtitle="12/26 EMA with 9-period signal"
                >
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart
                      data={macdChartData}
                      margin={{ top: 5, right: 10, left: -10, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.gridLine} />
                      <XAxis
                        dataKey="date"
                        tickFormatter={shortenDate}
                        minTickGap={40}
                        tick={commonAxisProps}
                      />
                      <YAxis tick={commonAxisProps} />
                      <Tooltip />
                      <Legend />
                      <ReferenceLine y={0} stroke={CHART_COLORS.refLine} />

                      {/* Histogram bars — green when positive, red when negative */}
                      <Bar dataKey="Histogram" barSize={2}>
                        {macdChartData.map((dataPoint, index) => {
                          const isPositive = (dataPoint.Histogram ?? 0) >= 0;
                          return (
                            <Cell
                              key={index}
                              fill={isPositive ? CHART_COLORS.bullish : CHART_COLORS.bearish}
                            />
                          );
                        })}
                      </Bar>

                      {/* MACD and Signal lines overlaid on the histogram */}
                      <Line
                        type="monotone"
                        dataKey="MACD"
                        stroke={CHART_COLORS.close}
                        strokeWidth={1.5}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="Signal"
                        stroke={CHART_COLORS.macdSignal}
                        strokeWidth={1.5}
                        dot={false}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>

                {/* RSI Indicator */}
                <ChartCard
                  title="Relative Strength Index (RSI)"
                  subtitle="14-period, overbought/oversold bands"
                >
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart
                      data={rsiChartData}
                      margin={{ top: 5, right: 10, left: -10, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.gridLine} />
                      <XAxis
                        dataKey="date"
                        tickFormatter={shortenDate}
                        minTickGap={40}
                        tick={commonAxisProps}
                      />
                      <YAxis domain={[0, 100]} tick={commonAxisProps} />
                      <Tooltip />

                      {/* Overbought line at 70 */}
                      <ReferenceLine
                        y={70}
                        stroke={CHART_COLORS.bearish}
                        strokeDasharray="4 4"
                        label={{ value: "70", fontSize: 10, fill: CHART_COLORS.bearish }}
                      />

                      {/* Oversold line at 30 */}
                      <ReferenceLine
                        y={30}
                        stroke={CHART_COLORS.bullish}
                        strokeDasharray="4 4"
                        label={{ value: "30", fontSize: 10, fill: CHART_COLORS.bullish }}
                      />

                      <Line
                        type="monotone"
                        dataKey="RSI"
                        stroke={CHART_COLORS.rsi}
                        strokeWidth={1.8}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </ChartCard>
              </div>

              {/* ── Monthly Trading Volume (Horizontal Bar Chart) ────────── */}
              <ChartCard
                title="Monthly Trading Volume"
                subtitle="Aggregated share volume by month"
                right={<Activity className="h-5 w-5 text-slate-300" />}
              >
                <ResponsiveContainer width="100%" height={340}>
                  <BarChart
                    data={monthlyVolumeData}
                    layout="vertical"
                    margin={{ top: 5, right: 20, left: 30, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.gridLine} />
                    <XAxis
                      type="number"
                      tickFormatter={formatCompact}
                      tick={commonAxisProps}
                    />
                    <YAxis
                      type="category"
                      dataKey="month"
                      width={80}
                      tick={{ fontSize: 11, fill: "#64748b" }}
                    />
                    <Tooltip
                      formatter={(value) =>
                        typeof value === "number" ? formatCompact(value) : "-"
                      }
                    />
                    <Bar
                      dataKey="volume"
                      fill={AXIS_BRAND_COLOR}
                      radius={[0, 4, 4, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* ── Recent Data Table ────────────────────────────────────── */}
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
                      {enrichedBars
                        .slice(-12)
                        .reverse()
                        .map((bar) => {
                          const isPositiveDay = bar.dailyReturnPct >= 0;
                          const changeColor = isPositiveDay
                            ? "text-green-600"
                            : "text-red-600";

                          return (
                            <tr
                              key={bar.date}
                              className="border-b border-slate-100 last:border-0 hover:bg-slate-50"
                            >
                              <td className="px-3 py-2 text-slate-600">
                                {bar.date}
                              </td>
                              <td className="px-3 py-2 text-right text-slate-600">
                                {bar.open.toFixed(2)}
                              </td>
                              <td className="px-3 py-2 text-right text-slate-600">
                                {bar.high.toFixed(2)}
                              </td>
                              <td className="px-3 py-2 text-right text-slate-600">
                                {bar.low.toFixed(2)}
                              </td>
                              <td className="px-3 py-2 text-right font-medium text-slate-800">
                                {bar.close.toFixed(2)}
                              </td>
                              <td className={`px-3 py-2 text-right font-medium ${changeColor}`}>
                                {isPositiveDay ? "+" : ""}
                                {bar.dailyReturnPct.toFixed(2)}%
                              </td>
                              <td className="px-3 py-2 text-right text-slate-600">
                                {bar.rsi?.toFixed(1) ?? "-"}
                              </td>
                              <td className="px-3 py-2 text-right text-slate-500">
                                {formatCompact(bar.volume)}
                              </td>
                            </tr>
                          );
                        })}
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
