import Navbar from '@/components/Navbar';
import CalendarComponent from '@/components/CalendarComponent';

export default function CalendarPage() {
    return (
        <main>
            <Navbar />
            <div className="container mx-auto mt-5">
                <h1 className="text-2xl font-bold mb-4">On-Call Duty Planner</h1>
                <CalendarComponent />
            </div>
        </main>
    );
}
