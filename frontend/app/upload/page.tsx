export default function UploadPage() {
  return (
    <main style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Upload File</h1>
      <p>Upload a CSV or PDF to begin AI-powered ingestion.</p>
      <div
        style={{
          border: "2px dashed #ccc",
          borderRadius: "8px",
          padding: "2rem",
          textAlign: "center",
          marginTop: "1rem",
        }}
      >
        <p>Drag & drop your file here, or click to browse</p>
        <input type="file" accept=".csv,.pdf" style={{ marginTop: "1rem" }} />
      </div>
    </main>
  );
}