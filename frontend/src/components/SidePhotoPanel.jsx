import '../styles/SidePhotoPanel.css'

// Right-side photo panel with a stat card overlay, used on steps whose
// design includes it (currently step 3).
export default function SidePhotoPanel({ backgroundImage, label, value, caption }) {
  return (
    <div className="spp-panel">
      <div className="spp-image" style={backgroundImage ? { backgroundImage: `url(${backgroundImage})` } : undefined} />
      <div className="spp-scrim" />
      <div className="spp-stat">
        <span className="spp-stat-label">{label}</span>
        <span className="spp-stat-value">{value}</span>
        <span className="spp-stat-caption">{caption}</span>
      </div>
    </div>
  )
}
