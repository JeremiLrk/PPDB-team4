import { useNavigate } from "react-router-dom";
import useClubs from "@/hooks/useClubs";
import { useSportTypes } from "@/hooks/useSportTypes";

function Clubs() {
  const navigate = useNavigate();
  const { clubs = [], loading: clubsLoading, error: clubsError } = useClubs();
  const { sportTypes = [], loading: sportsLoading, error: sportsError } = useSportTypes();

  const loading = clubsLoading || sportsLoading;
  const error = clubsError || sportsError;

  const theme = {
    container: { maxWidth: '1000px', margin: '0 auto', padding: '4rem 2rem', color: '#fff' },
    title: { fontSize: '2.5rem', fontWeight: '700', marginBottom: '0.5rem' },
    subtitle: { color: '#94a3b8', marginBottom: '2rem', fontSize: '1rem' },
    sportSection: { marginBottom: '3rem' },
    sportTitle: { fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#fff' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' },
    card: {
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '1.25rem 1.5rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', // Deep navy transparent
      border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px',
      cursor: 'pointer', transition: 'all 0.2s ease', backdropFilter: 'blur(10px)',
      width: '100%', outline: 'none'
    },
    clubName: { fontSize: '1.1rem', fontWeight: '600', color: '#f8fafc' },
    clubCity: { fontSize: '0.9rem', color: '#64748b' }
  };

  if (loading) return <div style={theme.container}>Loading...</div>;
  if (error) return <div style={theme.container}>{error}</div>;

  return (
    <section style={theme.container}>
      <h2 style={theme.title}>All Clubs</h2>
      <p style={theme.subtitle}>Kies een club om de club-homepage te openen, of start je eigen club!</p>

      {sportTypes.map((sport) => {
        const filteredClubs = clubs.filter(c => c.sport_type_id === sport.id);
        if (filteredClubs.length === 0) return null;

        return (
          <div key={sport.id} style={theme.sportSection}>
            <h3 style={theme.sportTitle}>{sport.name}</h3>
            <div style={theme.grid}>
              {filteredClubs.map((club) => (
                <button
                  key={club.id}
                  onClick={() => navigate(`/clubs/${club.id}`)}
                  style={theme.card}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(30, 41, 59, 0.8)';
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.3)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(15, 23, 42, 0.6)';
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                  }}
                >
                  <span style={theme.clubName}>{club.name}</span>
                  <span style={theme.clubCity}>{club.city}</span>
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </section>
  );
}

export default Clubs;