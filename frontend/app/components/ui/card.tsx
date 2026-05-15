export default function Card({ children, variant = "default" }: { children: React.ReactNode; variant?: "default" | "elevated" }) {
  const styles = {
    default: { border: "1px solid #e5e7eb", borderRadius: "8px", padding: "1rem" },
    elevated: { border: "1px solid #e5e7eb", borderRadius: "8px", padding: "1rem", boxShadow: "0 2px 8px rgba(0,0,0,0.1)" },
  };
  return <div style={styles[variant]}>{children}</div>;
}