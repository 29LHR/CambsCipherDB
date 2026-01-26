"""
Script to seed the database with initial challenges.
Run this after starting the app once to create the database.
"""
from app import app, db, Challenges
from datetime import datetime

# Sample challenges - customize these as needed
# release_time and closing_time can be None (always open) or datetime objects
challenges_data = [
    {
        "id": 1,
        "title": "Introduction",
        "published": True,
        "ciphertext": "Jryy qbar sbe penpxvat gur EBG-guvegrra pvcure va guvf vagebqhpgvba gb gur Pnzof Pvcure. Trg ernql sbe gur zvk bs qvnevrf, yrggref naq bgure svpgvbany fgngrzragf pbzvat lbhe jnl guebhtubhg gur pbhefr bs gurfr punyyratrf. Tbbq yhpx naq znl gur bqqf or rire va lbhe snibhe. C.F. Jura fbyivat gur punyyratrf znxr fher gb yrnir nal zvfgnxrf va fcryyvat naq tenzzne gung jr zvtug’ir yrsg va gurer gb gevpx lbh nybat jvgu cnqqvat punenpgref vs arprffnel nygubhtu chapghngvba naq pnfvat vf pbzcyrgryl gnxra bhg va znexvat.",
        "plaintext": "Well done for cracking the ROT-thirteen cipher in this introduction to the Cambs Cipher. Get ready for the mix of diaries, letters and other fictional statements coming your way throughout the course of these challenges. Good luck and may the odds be ever in your favour. P.S. When solving the challenges make sure to leave any mistakes in spelling and grammar that we might’ve left in there to trick you along with padding characters if necessary although punctuation and casing is completely taken out in marking.",
        "tips": "This is a Caesar cipher with a shift of 13. Each letter is shifted forward by 13 positions in the alphabet.",
        "points_reward": 0,
        "release_time": None,  # Always available
        "closing_time": None   # Never closes
    },
    {
        "id": 2,
        "title": "Challenge 1 (Practice)",
        "published": False,
        "ciphertext": "WKH TXLFN EURZQ IRA MXPSV RYHU WKH ODCB GRJ",
        "plaintext": "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
        "tips": "Another Caesar cipher. Try different shift values!",
        "points_reward": 0,
        "release_time": datetime(2025, 12, 28, 21, 0),
        "closing_time": datetime(2025, 12, 28, 21, 40)
    },
    {
        "id": 3,
        "title": "Challenge 2 (Practice)",
        "published": False,
        "ciphertext": "GUVF VF N FRPERG ZRFFNTR",
        "plaintext": "THIS IS A SECRET MESSAGE",
        "tips": "This is a ROT13 cipher - each letter is shifted by 13 positions.",
        "points_reward": 0,
        "release_time": datetime(2025, 12, 29, 21, 0),
        "closing_time": datetime(2025, 12, 29, 21, 40)
    },
    {
        "id": 4,
        "title": "Challenge 3 (Practice)",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 0,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 5,
        "title": "Challenge 4",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 15,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 6,
        "title": "Challenge 5",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 30,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 7,
        "title": "Challenge 6",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 45,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 8,
        "title": "Challenge 7",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 60,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 9,
        "title": "Challenge 8",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 75,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 10,
        "title": "Challenge 9",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 90,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 11,
        "title": "Challenge 10",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 105,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 12,
        "title": "Challenge 11",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 120,
        "release_time": None,
        "closing_time": None
    }
]

with app.app_context():
    # Clear existing challenges
    Challenges.query.delete()
    
    # Add new challenges
    for data in challenges_data:
        challenge = Challenges(
            id=data["id"]-1,  # Adjusting ID to be zero-based # type: ignore
            title=data["title"], # type: ignore
            published=data["published"], # type: ignore
            ciphertext=data["ciphertext"], # type: ignore
            plaintext=data["plaintext"], # type: ignore
            tips=data["tips"], # type: ignore
            points_reward=data["points_reward"], # type: ignore
            release_time=data["release_time"], # type: ignore
            closing_time=data["closing_time"] # type: ignore
        )
        db.session.add(challenge)
    
    db.session.commit()
    print(f"Successfully added {len(challenges_data)} challenges!")
    
    # Show summary
    published = Challenges.query.filter_by(published=True).count()
    unpublished = Challenges.query.filter_by(published=False).count()
    print(f"Published: {published}, Unpublished: {unpublished}")
