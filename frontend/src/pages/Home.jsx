const features = [
  { icon: 'bi-telephone-inbound', title: 'Answers Every Call', text: 'Ava picks up 24/7 so no customer is ever left waiting.' },
  { icon: 'bi-calendar-check', title: 'Books Appointments', text: 'Schedules, reschedules and confirms bookings automatically.' },
  { icon: 'bi-chat-dots', title: 'Handles Questions', text: 'Gives instant, accurate answers about your business.' },
]

export default function Home() {
  return (
    <>
      <section className="bg-primary text-white py-5">
        <div className="container py-5 text-center">
          <h1 className="display-4 fw-bold">Ava,  AI Receptionist</h1>
          <p className="lead col-lg-8 mx-auto my-4">
             Books appointments for your business, answers questions, and never misses a call.
          </p>
          
        </div>
      </section>

      <section id="features" className="py-5">
        <div className="container">
          <h2 className="text-center fw-bold mb-5">What Ava Can Do</h2>
          <div className="row g-4">
            {features.map((f) => (
              <div className="col-md-4" key={f.title}>
                <div className="card h-100 border-0 shadow-sm text-center p-4">
                  <i className={`bi ${f.icon} display-5 text-primary`}></i>
                  <h5 className="mt-3">{f.title}</h5>
                  <p className="text-muted mb-0">{f.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      
    </>
  )
}
