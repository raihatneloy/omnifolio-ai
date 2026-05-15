export default function Home() {
  return (
    <main style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Omnifolio AI</h1>
      <p>Privacy-first portfolio aggregator with AI-powered ingestion.</p>
      <nav style={{ marginTop: "1rem" }}>
        <a href="/upload" style={{ marginRight: "1rem" }}>Upload</a>
        <a href="/dashboard" style={{ marginRight: "1rem" }}>Dashboard</a>
        <a href="/review">Review</a>
      </nav>
    </main>
  );
}