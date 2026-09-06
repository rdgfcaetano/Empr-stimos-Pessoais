import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Bell, CircleDollarSign, FileClock, LayoutDashboard, LogOut, Moon, Pencil, Plus, Search, Shield, Sun, Trash2, Users } from "lucide-react";
import { brl, clearSession, Client, currentUser, Dashboard, Loan, Payment, request, setSession, User } from "./services/api";
import "./styles.css";

type View = "dashboard" | "clients" | "loans" | "admin";
type ClientForm = { name: string; phone: string; address: string; notes: string };
type LoanForm = { client_id: string; principal: string; interest_rate: string; interest_type: "monthly" | "daily" | "both"; loan_date: string; due_date: string; late_fee: string; late_interest_rate: string; status?: Loan["status"] };

const blankClient: ClientForm = { name: "", phone: "", address: "", notes: "" };
const today = () => new Date().toISOString().slice(0, 10);
const blankLoan = (): LoanForm => ({ client_id: "", principal: "", interest_rate: "10", interest_type: "monthly", loan_date: today(), due_date: "", late_fee: "0", late_interest_rate: "0", status: "open" });
const statusLabel: Record<string, string> = { open: "Aberto", paid: "Pago", overdue: "Atrasado", renegotiated: "Renegociado", admin: "Admin", partner: "Socio" };

function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("admin@local");
  const [password, setPassword] = useState("Admin123!");
  const [error, setError] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const data = await request<{ access_token: string; user: User }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      setSession(data.access_token, data.user);
      onLogin();
    } catch (err) {
      setError((err as Error).message);
    }
  }
  return <main className="login"><form onSubmit={submit} className="loginBox">
    <h1>Gestao de Emprestimos</h1>
    <label>Email<input value={email} onChange={e => setEmail(e.target.value)} /></label>
    <label>Senha<input type="password" value={password} onChange={e => setPassword(e.target.value)} /></label>
    {error && <p className="error">{error}</p>}
    <button>Entrar</button>
  </form></main>;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return <section className="stat"><span>{label}</span><strong>{value}</strong></section>;
}

function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  useEffect(() => { request<Dashboard>("/dashboard").then(setData); }, []);
  if (!data) return <p>Carregando...</p>;
  const max = Math.max(...data.monthly.map(m => Number(m.loaned) + Number(m.received)), 1);
  return <><div className="grid stats">
    <Stat label="Total emprestado" value={brl(data.total_loaned)} />
    <Stat label="Total recebido" value={brl(data.total_received)} />
    <Stat label="Lucro" value={brl(data.profit)} />
    <Stat label="Clientes" value={data.client_count} />
    <Stat label="Emprestimos ativos" value={data.active_loan_count} />
    <Stat label="Inadimplentes" value={data.overdue_count} />
  </div>
  <section className="panel chart"><h2>Movimento mensal</h2>{data.monthly.length === 0 && <small>Nenhum movimento ainda.</small>}{data.monthly.map(m => <div key={m.month} className="barRow"><span>{m.month}</span><div><i style={{ width: `${(Number(m.loaned) / max) * 100}%` }} /><b style={{ width: `${(Number(m.received) / max) * 100}%` }} /></div><small>{brl(m.loaned)} / {brl(m.received)}</small></div>)}</section></>;
}

function Toolbar({ q, setQ }: { q: string; setQ: (v: string) => void }) {
  return <div className="toolbar"><Search size={18} /><input placeholder="Pesquisar" value={q} onChange={e => setQ(e.target.value)} /></div>;
}

function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState<Client | null>(null);
  const [form, setForm] = useState<ClientForm>(blankClient);
  const load = () => request<Client[]>("/clients").then(setClients);
  useEffect(() => { load(); }, []);
  function edit(client: Client) {
    setEditing(client);
    setForm({ name: client.name, phone: client.phone, address: client.address || "", notes: client.notes || "" });
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    await request<Client>(editing ? `/clients/${editing.id}` : "/clients", { method: editing ? "PUT" : "POST", body: JSON.stringify(form) });
    setEditing(null);
    setForm(blankClient);
    load();
  }
  async function remove(id: number) {
    if (confirm("Excluir cliente?")) { await request(`/clients/${id}`, { method: "DELETE" }); load(); }
  }
  const rows = clients.filter(c => `${c.name} ${c.phone}`.toLowerCase().includes(q.toLowerCase()));
  return <div className="split"><form onSubmit={save} className="panel"><h2>{editing ? "Editar cliente" : "Novo cliente"}</h2>
    <input placeholder="Nome" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
    <input placeholder="Telefone" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} required />
    <input placeholder="Endereco" value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} />
    <textarea placeholder="Observacoes" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
    <div className="actions"><button><Plus size={18} />Salvar</button>{editing && <button type="button" className="secondary" onClick={() => { setEditing(null); setForm(blankClient); }}>Cancelar</button>}</div>
  </form><section className="panel wide"><Toolbar q={q} setQ={setQ} /><table><tbody>{rows.map(c => <tr key={c.id}><td><b>{c.name}</b><small>{c.phone}</small></td><td>{c.address}</td><td className="rowActions"><button className="icon edit" onClick={() => edit(c)}><Pencil size={16} /></button><button className="icon" onClick={() => remove(c.id)}><Trash2 size={16} /></button></td></tr>)}</tbody></table></section></div>;
}

function LoansPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [selected, setSelected] = useState<Loan | null>(null);
  const [editing, setEditing] = useState<Loan | null>(null);
  const [status, setStatus] = useState("all");
  const [form, setForm] = useState<LoanForm>(blankLoan());
  const [payment, setPayment] = useState({ amount: "", paid_at: today(), notes: "" });
  const load = () => { request<Loan[]>("/loans").then(setLoans); request<Client[]>("/clients").then(setClients); };
  useEffect(() => { load(); }, []);
  const clientName = (id: number) => clients.find(c => c.id === id)?.name || `Cliente #${id}`;
  function edit(loan: Loan) {
    setEditing(loan);
    setForm({ client_id: String(loan.client_id), principal: String(loan.principal), interest_rate: String(loan.interest_rate), interest_type: loan.interest_type, loan_date: loan.loan_date, due_date: loan.due_date, late_fee: String(loan.late_fee), late_interest_rate: String(loan.late_interest_rate), status: loan.status });
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    await request<Loan>(editing ? `/loans/${editing.id}` : "/loans", { method: editing ? "PUT" : "POST", body: JSON.stringify({ ...form, client_id: Number(form.client_id) }) });
    setEditing(null);
    setForm(blankLoan());
    load();
  }
  async function selectLoan(loan: Loan) {
    setSelected(loan);
    setPayments(await request<Payment[]>(`/loans/${loan.id}/payments`));
  }
  async function pay(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    await request<Payment>(`/loans/${selected.id}/payments`, { method: "POST", body: JSON.stringify(payment) });
    setPayment({ amount: "", paid_at: today(), notes: "" });
    await selectLoan(selected);
    load();
  }
  async function remove(id: number) {
    if (confirm("Excluir emprestimo?")) { await request(`/loans/${id}`, { method: "DELETE" }); setSelected(null); load(); }
  }
  const rows = loans.filter(l => status === "all" || l.status === status);
  return <div className="loansGrid"><form onSubmit={save} className="panel"><h2>{editing ? "Editar emprestimo" : "Novo emprestimo"}</h2>
    <select value={form.client_id} onChange={e => setForm({ ...form, client_id: e.target.value })} required><option value="">Cliente</option>{clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
    <input placeholder="Valor" type="number" step="0.01" value={form.principal} onChange={e => setForm({ ...form, principal: e.target.value })} required />
    <input placeholder="Taxa de juros %" type="number" step="0.01" value={form.interest_rate} onChange={e => setForm({ ...form, interest_rate: e.target.value })} />
    <select value={form.interest_type} onChange={e => setForm({ ...form, interest_type: e.target.value as LoanForm["interest_type"] })}><option value="monthly">Mensal</option><option value="daily">Diario</option><option value="both">Ambos</option></select>
    <input type="date" value={form.loan_date} onChange={e => setForm({ ...form, loan_date: e.target.value })} />
    <input type="date" value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} required />
    <input placeholder="Multa por atraso" type="number" step="0.01" value={form.late_fee} onChange={e => setForm({ ...form, late_fee: e.target.value })} />
    <input placeholder="Juros atraso % ao dia" type="number" step="0.01" value={form.late_interest_rate} onChange={e => setForm({ ...form, late_interest_rate: e.target.value })} />
    {editing && <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value as Loan["status"] })}><option value="open">Aberto</option><option value="paid">Pago</option><option value="overdue">Atrasado</option><option value="renegotiated">Renegociado</option></select>}
    <div className="actions"><button><Plus size={18} />Salvar</button>{editing && <button type="button" className="secondary" onClick={() => { setEditing(null); setForm(blankLoan()); }}>Cancelar</button>}</div>
  </form><section className="panel wide"><div className="toolbar"><select value={status} onChange={e => setStatus(e.target.value)}><option value="all">Todos</option><option value="open">Abertos</option><option value="paid">Pagos</option><option value="overdue">Atrasados</option><option value="renegotiated">Renegociados</option></select></div><table><thead><tr><th>Cliente</th><th>Valor</th><th>Total devido</th><th>Situacao</th><th></th></tr></thead><tbody>{rows.map(l => <tr key={l.id} onClick={() => selectLoan(l)} className={selected?.id === l.id ? "selected" : ""}><td>{clientName(l.client_id)}</td><td>{brl(l.principal)}</td><td>{brl(l.totals?.total_due || 0)}</td><td><span className={`badge ${l.status}`}>{statusLabel[l.status]}</span></td><td className="rowActions"><button className="icon edit" onClick={e => { e.stopPropagation(); edit(l); }}><Pencil size={16} /></button><button className="icon" onClick={e => { e.stopPropagation(); remove(l.id); }}><Trash2 size={16} /></button></td></tr>)}</tbody></table></section>{selected && <section className="panel details"><h2>Pagamentos #{selected.id}</h2><form onSubmit={pay} className="payForm"><input placeholder="Valor pago" type="number" step="0.01" value={payment.amount} onChange={e => setPayment({ ...payment, amount: e.target.value })} required /><input type="date" value={payment.paid_at} onChange={e => setPayment({ ...payment, paid_at: e.target.value })} /><input placeholder="Observacoes" value={payment.notes} onChange={e => setPayment({ ...payment, notes: e.target.value })} /><button>Registrar</button></form>{payments.map(p => <p key={p.id}><b>{brl(p.amount)}</b><small>{new Date(`${p.paid_at}T00:00:00`).toLocaleDateString("pt-BR")} · {p.responsible_user_name || "Usuario"}</small></p>)}</section>}</div>;
}

function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [notes, setNotes] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "partner" as User["role"] });
  const load = () => { request<User[]>("/users").then(setUsers); request<any[]>("/notifications").then(setNotes); request<any[]>("/logs").then(setLogs); };
  useEffect(() => { load(); }, []);
  async function create(e: React.FormEvent) {
    e.preventDefault();
    await request<User>("/users", { method: "POST", body: JSON.stringify(form) });
    setForm({ name: "", email: "", password: "", role: "partner" });
    load();
  }
  async function toggle(user: User) {
    await request<User>(`/users/${user.id}`, { method: "PUT", body: JSON.stringify({ is_active: !user.is_active }) });
    load();
  }
  async function reset(user: User) {
    const password = prompt(`Nova senha para ${user.name}`);
    if (password) { await request<User>(`/users/${user.id}`, { method: "PUT", body: JSON.stringify({ password }) }); load(); }
  }
  return <div className="adminGrid"><form onSubmit={create} className="panel"><h2>Novo usuario</h2><input placeholder="Nome" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /><input placeholder="Email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required /><input placeholder="Senha" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required /><select value={form.role} onChange={e => setForm({ ...form, role: e.target.value as User["role"] })}><option value="partner">Socio</option><option value="admin">Admin</option></select><button>Cadastrar</button></form><section className="panel"><h2>Usuarios</h2>{users.map(u => <p key={u.id} className="adminLine"><span><b>{u.name}</b><small>{u.email} · {statusLabel[u.role]} · {u.is_active ? "ativo" : "bloqueado"}</small></span><span className="rowActions"><button className="small" onClick={() => toggle(u)}>{u.is_active ? "Bloquear" : "Ativar"}</button><button className="small secondary" onClick={() => reset(u)}>Senha</button></span></p>)}</section><section className="panel"><h2>Notificacoes</h2>{notes.map(n => <p key={n.id}><b>{n.title}</b><small>{n.message}</small></p>)}</section><section className="panel span"><h2>Logs</h2>{logs.map(l => <p key={l.id}><b>{l.action} · {l.entity} #{l.entity_id}</b><small>{new Date(l.created_at).toLocaleString("pt-BR")}</small></p>)}</section></div>;
}

function App() {
  const [user, setUser] = useState<User | null>(currentUser());
  const [view, setView] = useState<View>("dashboard");
  const [dark, setDark] = useState(true);
  const nav = useMemo(() => [{ id: "dashboard", label: "Dashboard", icon: LayoutDashboard }, { id: "clients", label: "Clientes", icon: Users }, { id: "loans", label: "Emprestimos", icon: CircleDollarSign }, ...(user?.role === "admin" ? [{ id: "admin", label: "Admin", icon: Shield }] : [])] as const, [user]);
  if (!user) return <Login onLogin={() => setUser(currentUser())} />;
  const Page = view === "clients" ? ClientsPage : view === "loans" ? LoansPage : view === "admin" ? AdminPage : DashboardPage;
  return <div className={dark ? "app dark" : "app"}><aside><h1>Renato Loans</h1>{nav.map(item => { const Icon = item.icon; return <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => setView(item.id as View)}><Icon size={18} />{item.label}</button>; })}<button onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}Tema</button><button onClick={() => { clearSession(); setUser(null); }}><LogOut size={18} />Sair</button></aside><main><header><div><small>{user.role === "admin" ? "Administrador" : "Socio"}</small><h2>{user.name}</h2></div><div className="headerIcons"><Bell /><FileClock /></div></header><Page /></main></div>;
}

createRoot(document.getElementById("root")!).render(<App />);
