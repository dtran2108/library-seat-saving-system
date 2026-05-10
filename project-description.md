# Library self study room seat saving system

## Problem background and target users
### Problem
1. Some people use their bags as placeholders and don’t return for a long time, depriving people of spare seats.
2. Students won’t know if there are seats remaining until they’re actually at the study, sometimes wasting students’ time.

### Target users
1. End Users (NSYSU students): students who will use the system to view real-time availability, reserve study spaces using their student ID credentials, and manage their upcoming bookings.
2. System Administrators (NSYSU Library Staff): library staff who will use the administrative dashboard to monitor daily occupancy, block off seats for maintenance, and manage user reservations.

## System scope
- User Authentication & Profiles: Registration, login, and password
management for library patrons and administrators using an email address or
student/library ID.
- Booking Engine: The ability for users to select an available spot, choose a
date, and reserve specific time slots (up to 4 hours per day).
- Booking Management: A user dashboard to view upcoming reservations,
cancel existing bookings, or modify time slots.
- Admin Dashboard: A control panel for library staff to block out seats for
maintenance, override bookings, and manage user accounts.
- Responsive Web Design: A web interface optimized to work smoothly on
both desktop browsers and mobile phone browsers.
- Interactive Seat Map: A digital, floor plan displaying the layout of desks,
computer stations.
- Real-Time Availability: Color-coded status indicators (e.g., green for
available, red for booked) showing the current booking status of each spot.

## Preliminary function list (use cases)
### NSYSU Students (End Users)
- Authentication: Account register / log in / log out
- Check in / check out
- Reserve a Spot: View a digital floor plan of the library showing real-time availability of self-study spots and select an available seat and confirm booking for a specific time frame.
- View personal reservations
- Modify reservation time
- Extend reservation time
- Cancel reservation time
- Search for available spots by time
- Report system

### NSYSU Library Staff (System Administrators)
- Authentication: Account register / log in / log out
- User Management: check the user’s information (name, student ID, number of bookings so far, etc)
- Seat Management: view/modify bookings
- Enable or disable the booking system when needed (e.g. close for holidays)

### System Functions
- User Penalty Management: View logs of users who "no-show" and
temporarily suspend their booking privileges.
- Auto-Release Seats: Automatically cancel a booking and return the seat to
"available" status if the student does not check in in 30 minutes

## For Agent
1. You are a full-stack developer, you should know what to do. Use best practices
2. Use Flask as the backend framework, use Jinja2 as the template engine
3. Use Tailwind CSS for styling
4. If anything is unclear, ask for clarification instead of making assumptions
5. Do not generate code for database connection or anything related to it since it will be provided later
6. The project is for my university course, so make sure it is well-structured and easy to understand. Use comments and docstrings to explain your code.
7. Carefully carry out research before doing anything.