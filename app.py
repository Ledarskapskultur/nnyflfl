import React, { useEffect, useMemo, useRef, useState, createContext, useContext } from "react";
import { useForm } from "react-hook-form";
import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";

// =====================================================================
## Självskattning – Funktionellt ledarskap (stabil TSX, inga oklch-färger)
// =====================================================================

// ---------- Färgpalett (HEX/RGB) ----------
const PALETTE = {
  eggshell: "#FAF7F0", // äggskalsvit bakgrund
  white: "#FFFFFF",
  text: "#111827",
  navy50: "#E6ECF3",
  navy300: "#6B86A3",
  navy600: "#0B1F3A", // sober navy
  navy700: "#09233F",
  gray100: "#F3F4F6",
  gray200: "#E5E7EB",
  gray300: "#D1D5DB",
  gray400: "#9CA3AF",
  gray700: "#374151",
  green: "#2E7D32",
  orange: "#F59E0B",
};

// --- Power Automate webhook (anonym URL med sig=) ---
// Byt endast om du roterar nyckeln i PA; denna kommer från dig.
const WEBHOOK_URL = "https://default1ad3791223f4412ea6272223201343.20.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/bff5923897b04a39bc6ba69ea4afde69/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=B1rjO0FhY0ZxXO8VJvWPmcLAv-LMCgICG6tDguPmhwQ";
const WEBHOOK_SECRET = ""; // valfritt: använd om du lagt en Condition på secret i flödet

// ---------- Typer ----------
type Answers = { [q: number]: number };

type Contact = {
  name: string;
  company?: string;
  email: string;
};

type Scores = {
  listening: number; // Aktivt lyssnande (1-7)
  feedback: number;  // Återkoppling (8-15)
  goal: number;      // Målinriktning (16-20)
  total: number;     // Totalmedel (1-20)
};

// ---------- Hjälpfunktioner ----------
const mean = (nums: number[]) => (nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : 0);

const classify = (score: number) => {
  if (score >= 5.0) return { label: "Högt", hex: PALETTE.navy600 };
  if (score >= 2.5) return { label: "Medel", hex: PALETTE.navy300 };
  return { label: "Lågt", hex: PALETTE.gray400 };
};

const svDate = (date = new Date()) => new Intl.DateTimeFormat("sv-SE", { dateStyle: "long" }).format(date);

// Filvänligt datum (YYYYMMDD eller YYYY-MM-DD), används i filnamn och testas i självtester
const svDateFile = (d: Date = new Date()) => {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  // utan bindestreck för kompakta filnamn; självtest tillåter även med bindestreck
  return `${yyyy}${mm}${dd}`;
};

// Skapar ett unikt ID för varje mätning (ex: FL-20251010-125123-AB12)
const generateMeasurementId = () => {
  const d = new Date();
  const stamp = `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}-${String(d.getHours()).padStart(2,'0')}${String(d.getMinutes()).padStart(2,'0')}${String(d.getSeconds()).padStart(2,'0')}`;
  const rand = Math.random().toString(36).slice(2,6).toUpperCase();
  return `FL-${stamp}-${rand}`;
};

const sumRange = (answers: Answers, from: number, to: number): number => {
  let s = 0;
  for (let i = from; i <= to; i++) s += answers[i] ?? 0;
  return s;
};

// --- POST till Power Automate webhook ---
async function postToWebhook(
  url: string,
  contact: Contact,
  answers: Answers,
  secret?: string,
  pdf?: { pdfBase64: string; fileName: string },
  titleOverride?: string
) {
  if (!url || !url.includes("sig=")) {
    console.warn("Webhook URL saknas eller är inte anonym (ingen sig= hittad)");
    return; // gör inget om URL inte är korrekt ännu
  }

  const hasPdf = !!(pdf && pdf.pdfBase64 && pdf.pdfBase64.length > 0);
  const payload: any = {
    title: titleOverride ?? contact.email, // SharePoint-kolumn "Rubrik"
    name: contact.name,
    company: contact.company ?? "",
    email: contact.email,
    sumListening: sumRange(answers, 1, 7),
    sumFeedback: sumRange(answers, 8, 15),
    sumGoal: sumRange(answers, 16, 20),
    answersJson: JSON.stringify(answers),
    submittedAt: new Date().toISOString(),
    secret: secret ?? undefined,
    hasPdf,
  };
  if (hasPdf) {
    payload.pdfBase64 = pdf!.pdfBase64;
    payload.fileName = pdf!.fileName;
  }

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const txt = await res.text().catch(() => "");
      throw new Error(`Webhook POST misslyckades: ${res.status} ${txt}`);
    }
  } catch (e) {
    console.warn("Kunde inte posta till Power Automate:", e);
  }
}

// ---------- Kontext för state ----------
const AppStateCtx = createContext<{
  answers: Answers;
  setAnswer: (q: number, v: number) => void;
  reset: () => void;
} | null>(null);

const AppStateProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [answers, setAnswers] = useState<Answers>(() => {
    try {
      const raw = localStorage.getItem("fl_sjalvskattning_answers");
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem("fl_sjalvskattning_answers", JSON.stringify(answers));
    } catch {}
  }, [answers]);

  const setAnswer = (q: number, v: number) => setAnswers(prev => ({ ...prev, [q]: v }));
  const reset = () => setAnswers({});

  return (
    <AppStateCtx.Provider value={{ answers, setAnswer, reset }}>
      {children}
    </AppStateCtx.Provider>
  );
};

const useAppState = () => {
  const ctx = useContext(AppStateCtx);
  if (!ctx) throw new Error("useAppState must be used within provider");
  return ctx;
};

// ---------- Frågorna ----------
## 1–7 Aktivt lyssnande, 8–15 Återkoppling, 16–20 Målinriktning
const QUESTIONS: { id: number; text: string }[] = [
  { id: 1, text: "Jag bjuder aktivt in medarbetare till dialog och idéer." },
  { id: 2, text: "Jag ställer öppna frågor för att förstå olika perspektiv." },
  { id: 3, text: "Jag sammanfattar vad jag hört för att säkerställa förståelse." },
  { id: 4, text: "Jag bekräftar andras bidrag och visar att jag lyssnar." },
  { id: 5, text: "Jag använder information från medarbetare i beslut." },
  { id: 6, text: "Jag skapar utrymme för alla röster i möten." },
  { id: 7, text: "Jag anpassar min kommunikation utifrån mottagarens behov." },
  { id: 8, text: "Jag uttrycker förväntningar tydligt och i rätt tid." },
  { id: 9, text: "Jag ger konkret återkoppling kopplad till beteenden och resultat." },
  { id: 10, text: "Jag följer upp överenskommelser och stöttar vid behov." },
  { id: 11, text: "Jag uppmärksammar framsteg och förstärker önskat beteende." },
  { id: 12, text: "Jag korrigerar respektfullt när något inte fungerar." },
  { id: 13, text: "Jag säkerställer att budskapet är förstått (t.ex. genom frågor)." },
  { id: 14, text: "Jag anpassar återkopplingens form (muntligt, skriftligt, 1:1)." },
  { id: 15, text: "Jag dokumenterar och synliggör uppföljning när det behövs." },
  { id: 16, text: "Jag formulerar tydliga mål och prioriteringar." },
  { id: 17, text: "Jag fördelar ansvar och befogenheter på ett tydligt sätt." },
  { id: 18, text: "Jag säkerställer att teamet vet hur målen mäts." },
  { id: 19, text: "Jag följer upp resultat regelbundet och transparent." },
  { id: 20, text: "Jag justerar plan och resurser utifrån lägesbild och data." },
];

const SCALE_LABELS = [
  "1 Aldrig",
  "2 Nästan aldrig",
  "3 Sällan",
  "4 Ibland",
  "5 Ofta",
  "6 Nästan alltid",
  "7 Alltid",
];

// ---------- UI-komponenter ----------
const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <div className={`rounded-2xl shadow p-6 ${className ?? ""}`} style={{ background: PALETTE.white }}>
    {children}
  </div>
);

const PrimaryButton: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ className, children, ...props }) => (
  <button
    className={`px-5 py-3 rounded-xl font-medium transition disabled:opacity-50 ${className ?? ""}`}
    style={{ background: PALETTE.navy600, color: PALETTE.white }}
    {...props}
  >
    {children}
  </button>
);

const SecondaryButton: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ className, children, ...props }) => (
  <button
    type={(props as any).type ?? "button"}
    className={`px-5 py-3 rounded-xl font-medium transition disabled:opacity-50 ${className ?? ""}`}
    style={{ background: PALETTE.gray200, color: PALETTE.text }}
    {...props}
  >
    {children}
  </button>
);

// Panel med ram och titel – för rapportens boxar
const Panel: React.FC<{ title?: string; children: React.ReactNode; className?: string }> = ({ title, children, className }) => (
  <div className={`rounded-lg p-4 ${className ?? ""}`} style={{ background: PALETTE.white, border: `1px solid ${PALETTE.gray400}` }}>
    {title && <h3 className="text-lg font-semibold mb-2" style={{ color: PALETTE.navy700 }}>{title}</h3>}
    {children}
  </div>
);

// Högerkort: totalsumma (stor siffra) + stapel (summa vs total)
const CategoryRightCard: React.FC<{ title: string; sum: number; total: number }> = ({ title, sum, total }) => {
  const pct = Math.max(0, Math.min(100, (sum / total) * 100));
  return (
    <div className="rounded-xl p-4" style={{ background: PALETTE.white, border: `1px solid ${PALETTE.gray300}` }}>
      <div className="text-sm font-semibold" style={{ color: PALETTE.navy700 }}>{title}</div>
      <div className="text-3xl font-bold mt-1" style={{ color: PALETTE.text }}>{Math.round(sum)}</div>
      <div className="mt-3 space-y-2">
        <div className="w-full h-3 rounded" style={{ background: PALETTE.gray200 }} aria-label={`Summa ${Math.round(sum)} av ${total}`}>
          <div className="h-3 rounded" style={{ width: pct + "%", background: PALETTE.green }} />
        </div>
        <div className="w-full h-3 rounded" style={{ background: PALETTE.orange, opacity: 0.85 }} />
      </div>
      <div className="mt-2 text-xs" style={{ color: PALETTE.gray700 }}>Summa {Math.round(sum)}/{total}</div>
    </div>
  );
};

// ---------- Startvy ----------
const StartView: React.FC<{ onStart: () => void }> = ({ onStart }) => (
  <div className="max-w-3xl mx-auto">
    <Card>
      <h1 className="text-3xl md:text-4xl font-bold" style={{ color: PALETTE.navy700 }}>Självskattning – Funktionellt ledarskap</h1>
      <p className="mt-4 leading-relaxed" style={{ color: PALETTE.gray700 }}>
        Denna självskattning hjälper dig att reflektera över tre centrala områden i funktionellt ledarskap:
        <span className="font-medium"> aktivt lyssnande, återkoppling och målinriktning</span>. Du besvarar 20 påståenden på en 7-gradig skala.
        Efteråt får du en personlig rapport som PDF med text och reflektion.
      </p>
      <div className="mt-6">
        <PrimaryButton onClick={onStart}>Starta självskattning</PrimaryButton>
      </div>
    </Card>
  </div>
);

// ---------- Frågekomponent ----------
const Likert: React.FC<{ value?: number; onChange: (v: number) => void }> = ({ value, onChange }) => (
  <div className="grid grid-cols-7 gap-2 mt-3">
    {Array.from({ length: 7 }).map((_, i) => {
      const v = i + 1;
      const selected = value === v;
      return (
        <button
          key={v}
          type="button"
          onClick={() => onChange(v)}
          className={`text-sm md:text-base border rounded-lg py-2 px-1 text-center focus:outline-none`}
          style={{
            borderColor: selected ? PALETTE.navy600 : PALETTE.gray300,
            boxShadow: selected ? `0 0 0 3px rgba(11, 31, 58, 0.25)` : undefined,
            background: selected ? PALETTE.navy50 : PALETTE.white,
          }}
          aria-pressed={selected}
        >
          {v}
        </button>
      );
    })}
  </div>
);

const QuestionsView: React.FC<{ onDone: () => void }> = ({ onDone }) => {
  const { answers, setAnswer } = useAppState();
  const [page, setPage] = useState(0); // 0..3
  const pageSize = 5; const totalPages = 4;
  const items = useMemo(() => QUESTIONS.slice(page * pageSize, (page + 1) * pageSize), [page]);
  const allOnPageAnswered = items.every(q => answers[q.id] != null);
  const allAnswered = QUESTIONS.every(q => answers[q.id] != null);
  return (
    <div className="max-w-4xl mx-auto">
      <Card>
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold" style={{ color: PALETTE.navy700 }}>Frågor</h2>
          <div className="text-sm" style={{ color: PALETTE.gray700 }}>Steg {page + 1} av {totalPages}</div>
        </div>
        <div className="w-full rounded-full h-2 mt-2" style={{ background: PALETTE.gray200 }}>
          <div className="h-2 rounded-full" style={{ background: PALETTE.navy600, width: `${((page + 1) / totalPages) * 100}%` }} />
        </div>
        <ol className="mt-6 space-y-6">
          {items.map((q) => (
            <li key={q.id} className="border-b pb-4" style={{ borderColor: PALETTE.gray200 }}>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-semibold" style={{ background: PALETTE.navy600, color: PALETTE.white }}>{q.id}</div>
                <div className="flex-1">
                  <p className="font-medium" style={{ color: PALETTE.text }}>{q.text}</p>
                  <div className="mt-2 text-xs grid grid-cols-7" style={{ color: PALETTE.gray700 }}>
                    {SCALE_LABELS.map((s, i) => (<span key={s} className={`text-center ${i===0?"text-left":""}`}>{s.split(" ")[0]}</span>))}
                  </div>
                  <Likert value={answers[q.id]} onChange={(v)=>setAnswer(q.id, v)} />
                </div>
              </div>
            </li>
          ))}
        </ol>
        <div className="mt-6 flex items-center justify-between">
          <SecondaryButton onClick={()=>setPage(p=>Math.max(0,p-1))} disabled={page===0}>Föregående</SecondaryButton>
          {page < totalPages - 1 ? (
            <PrimaryButton onClick={()=>setPage(p=>Math.min(totalPages-1,p+1))} disabled={!allOnPageAnswered}>Nästa</PrimaryButton>
          ) : (
            <PrimaryButton onClick={onDone} disabled={!allAnswered}>Fortsätt</PrimaryButton>
          )}
        </div>
      </Card>
    </div>
  );
};

// ---------- Kontaktformulär ----------
const ContactForm: React.FC<{ onGenerate: (contact: Contact) => void }> = ({ onGenerate }) => {
  const { register, handleSubmit, formState: { errors } } = useForm<Contact>({ defaultValues: { name: "", company: "", email: "" } });
  return (
    <div className="max-w-xl mx-auto">
      <Card>
        <h2 className="text-2xl font-semibold" style={{ color: PALETTE.navy700 }}>Kontaktuppgifter</h2>
        <p className="mt-2" style={{ color: PALETTE.gray700 }}>Fyll i dina uppgifter för att generera din personliga rapport.</p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit(onGenerate)}>
          <div>
            <label className="block text-sm font-medium" style={{ color: PALETTE.text }}>Namn <span style={{ color: '#DC2626' }}>*</span></label>
            <input className="mt-1 w-full border rounded-lg px-3 py-2 focus:outline-none" style={{ borderColor: PALETTE.gray300 }} placeholder="För- och efternamn" {...register("name", { required: "Ange ditt namn" })} />
            {errors.name && <p className="text-sm mt-1" style={{ color: '#DC2626' }}>{errors.name.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium" style={{ color: PALETTE.text }}>Företag (valfritt)</label>
            <input className="mt-1 w-full border rounded-lg px-3 py-2 focus:outline-none" style={{ borderColor: PALETTE.gray300 }} placeholder="Organisation / Team" {...register("company")} />
          </div>
          <div>
            <label className="block text-sm font-medium" style={{ color: PALETTE.text }}>E-post <span style={{ color: '#DC2626' }}>*</span></label>
            <input type="email" className="mt-1 w-full border rounded-lg px-3 py-2 focus:outline-none" style={{ borderColor: PALETTE.gray300 }} placeholder="namn@foretag.se" {...register("email", { required: "Ange en giltig e-post", pattern: { value: /.+@.+\..+/, message: "Ogiltig e-post" } })} />
            {errors.email && <p className="text-sm mt-1" style={{ color: '#DC2626' }}>{errors.email.message}</p>}
          </div>
          <div className="pt-2"><PrimaryButton type="submit">Generera rapport</PrimaryButton></div>
        </form>
      </Card>
    </div>
  );
};

// ---------- Resultat & Rapport ----------
const ReportView: React.FC<{ contact: Contact; onRestart: () => void }> = ({ contact, onRestart }) => {
  const [measurementId, setMeasurementId] = useState<string | null>(null);
  const { answers } = useAppState();
  const reportRef = useRef<HTMLDivElement | null>(null);
  const [ctaBlocked, setCtaBlocked] = useState(false);
  const isEmbedded = useMemo(() => { try { return window.self !== window.top; } catch { return true; } }, []);

  // SUMMOR per kategori direkt från svaren
  const sum1to7 = useMemo(() => sumRange(answers, 1, 7), [answers]);
  const sum8to15 = useMemo(() => sumRange(answers, 8, 15), [answers]);
  const sum16to20 = useMemo(() => sumRange(answers, 16, 20), [answers]);

  // Bygg PDF och returnera Base64 + filnamn (för SharePoint-bilaga)
  const buildPdfBase64 = async (): Promise<{ base64: string; fileName: string }> => {
    if (!reportRef.current) throw new Error('Report root saknas');
    const input = reportRef.current as HTMLElement;
    input.style.background = PALETTE.eggshell;

    const canvas = await html2canvas(input, { scale: 2, useCORS: true, backgroundColor: PALETTE.eggshell });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const imgWidth = pageWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    let position = 0;
    let heightLeft = imgHeight;
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
    heightLeft -= pageHeight;

    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
      heightLeft -= pageHeight;
    }

    const fileName = `Självskattning_${contact.name.replace(/\s+/g, "_")}_${svDateFile(new Date())}.pdf`;
    const base64 = pdf.output('datauristring').replace(/^data:application\/pdf;base64,/, '');
    return { base64, fileName };
  };

  // Skicka rapporten (PDF) + data till Power Automate/SharePoint när rapporten visas
  useEffect(() => {
    (async () => {
      try {
        const id = generateMeasurementId();
        setMeasurementId(id);
        const { base64, fileName } = await buildPdfBase64();
        await postToWebhook(
          WEBHOOK_URL,
          contact,
          answers,
          WEBHOOK_SECRET,
          { pdfBase64: base64, fileName },
          id
        );
      } catch (e) {
        console.warn('Kunde inte skapa/skicka PDF till SharePoint:', e);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openBooking = () => {
    const url = "https://link.paidsocialfunnels.com/widget/bookings/carl-fredrik";
    setCtaBlocked(false);
    // 1) Ny flik
    let win: Window | null = null;
    try { win = window.open(url, "_blank", "noopener,noreferrer"); } catch {}
    if (win) return;
    // 2) Översta fönstret
    try { if (window.top) { (window.top as Window).location.href = url; return; } } catch {}
    // 3) Osynligt ankare
    try {
      const a = document.createElement('a');
      a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer';
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      return;
    } catch {}
    // 4) Visa länk att kopiera
    setCtaBlocked(true);
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-4 flex justify-between items-center">
        <div className="text-sm" style={{ color: PALETTE.gray700 }}>Genererad: {svDate()}</div>
        <div className="flex gap-2">
          <PrimaryButton onClick={onRestart}>Starta om</PrimaryButton>
        </div>
      </div>
      
      <Card>
        {/* WRAPPER: allt innehåll som ska in i PDF:en */}
        <div ref={reportRef} className="report-root font-sans p-4 rounded-xl" style={{ background: PALETTE.eggshell }}>
          {/* Titel */}
          <div className="rounded-lg p-4 mb-4" style={{ background: PALETTE.white, border: `1px solid ${PALETTE.gray400}` }}>
            <h1 className="text-3xl font-bold" style={{ color: PALETTE.navy700 }}>Din rapport – Funktionellt ledarskap</h1>
            <p style={{ color: PALETTE.gray700 }}>{svDate()}</p>
          </div>

          {/* Uppgifter */}
          <Panel title="Uppgifter">
            <dl>
              <div className="flex justify-between py-1" style={{ borderBottom: `1px solid ${PALETTE.gray200}` }}><dt className="font-medium">Rubrik (Mätnings-ID)</dt><dd>{measurementId}</dd></div>
              <div className="flex justify-between py-1" style={{ borderBottom: `1px solid ${PALETTE.gray200}` }}><dt className="font-medium">Namn</dt><dd>{contact.name}</dd></div>
              <div className="flex justify-between py-1" style={{ borderBottom: `1px solid ${PALETTE.gray200}` }}><dt className="font-medium">Företag</dt><dd>{contact.company || "—"}</dd></div>
              <div className="flex justify-between py-1" style={{ borderBottom: `1px solid ${PALETTE.gray200}` }}><dt className="font-medium">E-post</dt><dd>{contact.email}</dd></div>
            </dl>
          </Panel>

          {/* Delområden */}
          <div className="rounded-lg p-3 mt-3" style={{ background: PALETTE.white, border: `1px solid ${PALETTE.gray400}` }}>
            <h2 className="text-xl font-bold" style={{ color: PALETTE.navy700 }}>Delområden</h2>
          </div>

          {/* Aktivt lyssnande */}
          <div className="grid md:grid-cols-3 gap-4 items-start mt-3">
            <div className="md:col-span-2">
              <Panel title="Aktivt lyssnande">
                <p style={{ color: PALETTE.gray700 }}>
                  I dagens arbetsliv har chefens roll förändrats. Medarbetarna sitter ofta på den djupaste kompetensen och lösningarna på verksamhetens utmaningar.
                </p>
                <p className="mt-2" style={{ color: PALETTE.gray700 }}>
                  Därför är aktivt lyssnande en av chefens viktigaste färdigheter. Det handlar inte bara om att höra vad som sägs, utan om att förstå, visa intresse och använda den information du får. När du bjuder in till dialog och tar till dig medarbetarnas perspektiv visar du att deras erfarenheter är värdefulla.
                </p>
                <p className="mt-2" style={{ color: PALETTE.gray700 }}>
                  Genom att agera på det du hör – bekräfta, följa upp och omsätta idéer i handling – stärker du både engagemang, förtroende och delaktighet.
                </p>
              </Panel>
            </div>
            <CategoryRightCard title="Aktivt lyssnande" sum={sum1to7} total={49} />
          </div>

          {/* Återkoppling */}
          <div className="grid md:grid-cols-3 gap-4 items-start mt-3">
            <div className="md:col-span-2">
              <Panel title="Återkoppling">
                <p style={{ color: PALETTE.gray700 }}>
                  Effektiv återkoppling är grunden för både utveckling och motivation. Medarbetare behöver veta vad som förväntas, hur de ligger till och hur de kan växa. När du som chef tydligt beskriver uppgifter och förväntade beteenden skapar du trygghet och fokus i arbetet.
                </p>
                <p className="mt-2" style={{ color: PALETTE.gray700 }}>
                  Återkoppling handlar sedan om närvaro och uppföljning – att se, lyssna och ge både beröm och konstruktiv feedback. Genom att tydligt lyfta fram vad som fungerar och vad som kan förbättras, förstärker du önskvärda beteenden och hjälper dina medarbetare att lyckas.
                </p>
                <p className="mt-2" style={{ color: PALETTE.gray700 }}>
                  I svåra situationer blir återkopplingen extra viktig. Att vara lugn, konsekvent och tydlig när det blåser visar ledarskap på riktigt.
                </p>
              </Panel>
            </div>
            <CategoryRightCard title="Återkoppling" sum={sum8to15} total={56} />
          </div>

          {/* Målinriktning */}
          <div className="grid md:grid-cols-3 gap-4 items-start mt-6">
            <div className="md:col-span-2">
              <Panel title="Målinriktning">
                <p style={{ color: PALETTE.gray700 }}>
                  Målinriktat ledarskap handlar om att ge tydliga ramar – tid, resurser och ansvar – så att medarbetare kan arbeta effektivt och med trygghet. Tydliga och inspirerande mål skapar riktning och hjälper alla att förstå vad som är viktigt just nu.
                </p>
                <p className="mt-2" style={{ color: PALETTE.gray700 }}>
                  Som chef handlar det om att formulera mål som går att tro på, och att tydliggöra hur de ska nås. När du delegerar ansvar och befogenheter visar du förtroende och skapar engagemang. Målen blir då inte bara något att leverera på – utan något att vara delaktig i.
                </p>
                <p className="mt-2" style={{ color: PALETTE.gray700 }}>
                  Uppföljning är nyckeln. Genom att uppmärksamma framsteg, ge återkoppling och fira resultat förstärker du både prestation och motivation.
                </p>
              </Panel>
            </div>
            <CategoryRightCard title="Målinriktning" sum={sum16to20} total={35} />
          </div>

          {/* Nästa steg */}
          <Panel title="Nästa steg" className="mt-8">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2 p-2 rounded-lg" style={{ background: PALETTE.gray100, border: `1px solid ${PALETTE.gray300}` }}>
                <span className="text-sm font-medium" style={{ color: PALETTE.navy700 }}>Sammanfattning:</span>
                <span className="text-xs md:text-sm px-2 py-1 rounded-full" style={{ background: PALETTE.navy50, border: `1px solid ${PALETTE.navy300}`, color: PALETTE.navy700 }}>Aktivt lyssnande {Math.round(sum1to7)}/49</span>
                <span className="text-xs md:text-sm px-2 py-1 rounded-full" style={{ background: PALETTE.navy50, border: `1px solid ${PALETTE.navy300}`, color: PALETTE.navy700 }}>Återkoppling {Math.round(sum8to15)}/56</span>
                <span className="text-xs md:text-sm px-2 py-1 rounded-full" style={{ background: PALETTE.navy50, border: `1px solid ${PALETTE.navy300}`, color: PALETTE.navy700 }}>Målinriktning {Math.round(sum16to20)}/35</span>
              </div>

              <div>
                <p className="font-medium" style={{ color: PALETTE.navy700 }}>Aktivt lyssnande</p>
                <ul className="list-disc ml-6 mt-1" style={{ color: PALETTE.gray700 }}>
                  <li><strong>Aktivt lyssnande:</strong> träna på att använda kroppsspråk, frågor och återkoppling som visar att du verkligen lyssnar.</li>
                  <li className="mt-1"><strong>Hantera gnäll och kritik:</strong> lär dig hur du kan behålla lugnet, lyssna även i svåra samtal och styra dialogen mot lösningar.</li>
                </ul>
              </div>

              <div>
                <p className="font-medium" style={{ color: PALETTE.navy700 }}>Återkoppling</p>
                <ul className="list-disc ml-6 mt-1" style={{ color: PALETTE.gray700 }}>
                  <li><strong>Analys av beteenden i organisationen:</strong> förstå varför medarbetare agerar som de gör och hur du kan påverka beteenden konstruktivt.</li>
                  <li className="mt-1"><strong>Positiv förstärkning genom positiv återkoppling:</strong> träna på att ge beröm och förstärka rätt beteenden.</li>
                  <li className="mt-1"><strong>Korrigerande återkoppling:</strong> lär dig att ge kritik som leder till lärande och förbättring, inte försvar.</li>
                </ul>
              </div>

              <div>
                <p className="font-medium" style={{ color: PALETTE.navy700 }}>Målinriktning</p>
                <p className="mt-1" style={{ color: PALETTE.gray700 }}>
                  Målinriktat ledarskap handlar om att skapa riktning, struktur och tydlighet. Det betyder att formulera mål som är meningsfulla, realistiska och engagerande – och följa upp både resultat och beteenden på vägen.
                </p>
                <p className="mt-2" style={{ color: PALETTE.gray700 }}>
                  Fortsätt utvecklas genom att arbeta med:
                </p>
                <ul className="list-disc ml-6 mt-1" style={{ color: PALETTE.gray700 }}>
                  <li><strong>Hantera tid utifrån prioriteringar:</strong> hitta balans mellan akuta uppgifter och långsiktiga mål.</li>
                  <li className="mt-1"><strong>Funktionella mötesbeteenden:</strong> lär dig leda möten som skapar delaktighet och framdrift.</li>
                  <li className="mt-1"><strong>Formulera och följa upp mål:</strong> träna på att sätta tydliga, mätbara och inspirerande mål.</li>
                  <li className="mt-1"><strong>Funktionell problemlösning:</strong> använd mål- och lösningsfokus för att hantera hinder och skapa lärande i gruppen.</li>
                </ul>
              </div>

              <div>
                <p className="font-medium" style={{ color: PALETTE.navy700 }}>Självledarskap</p>
                <p className="mt-1" style={{ color: PALETTE.gray700 }}>
                  För att kunna använda funktionella ledarbeteenden i vardagen behöver du också kunna hantera egna tankar, känslor och fokus. Det handlar om att vara närvarande, flexibel och medveten om hur du själv påverkar ditt ledarskap.
                </p>
                <p className="mt-2" style={{ color: PALETTE.gray700 }}>Stärk din självinsikt genom att arbeta med:</p>
                <ul className="list-disc ml-6 mt-1" style={{ color: PALETTE.gray700 }}>
                  <li><strong>Flexibilitet i relation till tankar:</strong> lär dig hantera självkritiska eller begränsande tankar.</li>
                  <li className="mt-1"><strong>Medveten närvaro:</strong> träna din förmåga att fokusera och agera med lugn och tydlighet – även under press.</li>
                </ul>
              </div>
            </div>
          </Panel>
        </div>
      </Card>

      {/* CTA endast i rapportvyn */}
      <div className="px-4 pb-6 text-center">
        <button type="button" onClick={openBooking} className="inline-block px-5 py-3 rounded-xl font-medium" style={{ background: PALETTE.navy600, color: PALETTE.white, cursor: 'pointer' }}>
          Boka Strategimöte
        </button>
        {ctaBlocked && (
          <p className="mt-2 text-sm" style={{ color: PALETTE.gray700 }}>
            Din webbläsare blockerade öppningen av länken. Kopiera och klistra in i en ny flik:
            {' '}<a href="https://link.paidsocialfunnels.com/widget/bookings/carl-fredrik" target="_blank" rel="noopener noreferrer" style={{ color: PALETTE.navy700, textDecoration: 'underline' }}>https://link.paidsocialfunnels.com/widget/bookings/carl-fredrik</a>
          </p>
        )}
      </div>
    </div>
  );
};

// ---------- Huvudapp ----------
const App: React.FC = () => {
  const { answers, reset } = useAppState();
  const [step, setStep] = useState<"start" | "questions" | "contact" | "report">("start");
  const [contact, setContact] = useState<Contact | null>(null);

  const handleQuestionsDone = () => setStep("contact");

  const calcScores = (ans: Answers): Scores => {
    const listening = mean([1,2,3,4,5,6,7].map(i => ans[i] ?? 0));
    const feedback  = mean([8,9,10,11,12,13,14,15].map(i => ans[i] ?? 0));
    const goal      = mean([16,17,18,19,20].map(i => ans[i] ?? 0));
    const total     = mean(Object.values(ans));
    return { listening, feedback, goal, total };
  };

  // Viktigt: Vi POST:ar först när rapporten visas (då finns PDF). Ingen POST här för att undvika dubbletter.
  const handleGenerate = async (c: Contact) => {
    setContact(c);
    setStep("report");
  };

  const handleRestart = () => { reset(); setContact(null); setStep("start"); };

  // --- Självtester (enkla runtime-testfall) ---
  useEffect(() => {
    // 1) medelvärden & klassning
    console.assert(mean([1, 1, 1]) === 1, "mean ska bli 1");
    console.assert(classify(5.1).label === "Högt", "klassning >=5 ska vara Högt");
    console.assert(classify(2.6).label === "Medel", "klassning 2.5–4.9 ska vara Medel");
    console.assert(classify(1.9).label === "Lågt", "klassning <2.5 ska vara Lågt");

    // 2) summeringar
    const demo: Answers = {}; for (let i = 1; i <= 7; i++) demo[i] = 7; for (let i = 8; i <= 15; i++) demo[i] = 5; for (let i = 16; i <= 20; i++) demo[i] = 3;
    const s1 = sumRange(demo, 1, 7); const s2 = sumRange(demo, 8, 15); const s3 = sumRange(demo, 16, 20);
    console.assert(s1 === 49 && s2 === 40 && s3 === 15, "Summor ska bli 49/40/15");
    console.assert(sumRange({}, 1, 7) === 0, "Tomma svar ska ge 0 i summa");

    // 3) inga oklch-färger i palett/egna stilar
    console.assert(Object.values(PALETTE).every(v => typeof v === 'string' && !v.includes('oklch')), 'Paletten får inte innehålla oklch');
    const hasOklchInStyles = Array.from(document.querySelectorAll('style')).some(s => (s.textContent||'').includes('oklch('));
    console.assert(!hasOklchInStyles, 'Våra egna inbäddade stilar får inte använda oklch');

    // 4) procentklamp
    const overPct = Math.max(0, Math.min(100, (60/56)*100));
    const underPct = Math.max(0, Math.min(100, (-5/56)*100));
    console.assert(overPct === 100, 'Procenten ska clampas till 100 vid översumma');
    console.assert(underPct === 0, 'Procenten ska clampas till 0 vid negativ summa');

    // 5) inga regex-markörer i DOM
    const bodyHtml = document.body.innerHTML;
    console.assert(!bodyHtml.includes('$1') && !bodyHtml.includes('$2'), 'DOM får inte innehålla $1/$2-markörer');

    // 6) datumhelpers format (svDateFile ska ge 8–10 tecken inklusive bindestreck)
    const f = svDateFile(new Date());
    console.assert(/^\d{4}-?\d{2}-?\d{2}$/.test(f), 'svDateFile format felaktigt');
  }, []);

  return (
    <main className="min-h-screen" style={{ background: PALETTE.eggshell, color: PALETTE.text }}>
      <header className="max-w-5xl mx-auto px-4 py-6">
        <h1 className="text-xl md:text-2xl font-semibold" style={{ color: PALETTE.navy700 }}>Självskattning – Funktionellt ledarskap</h1>
      </header>
      <section className="px-4 pb-16">
        {step === "start" && <StartView onStart={() => setStep("questions")} />}
        {step === "questions" && <QuestionsView onDone={handleQuestionsDone} />}
        {step === "contact" && <ContactForm onGenerate={handleGenerate} />}
        {step === "report" && contact && (
          <ReportView contact={contact} onRestart={handleRestart} />
        )}
      </section>

      {/* (CTA är flyttad till ReportView; ingen global CTA här) */}

      <footer className="text-center text-xs py-8" style={{ color: PALETTE.gray700 }}>© {new Date().getFullYear()} Självskattning. Byggd med React, Tailwind, jsPDF.</footer>

      {/* Tailwind helper styles for print/PDF */}
      <style>{`
        .report-root { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Inter, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; }
        @media print { .break-before-page { break-before: page; } }
      `}</style>
    </main>
  );
};

// Exportera som default komponent för Canvas-förhandsvisning
export default function WrappedApp() {
  return (
    <AppStateProvider>
      <App />
    </AppStateProvider>
  );
}
