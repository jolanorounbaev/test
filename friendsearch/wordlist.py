import bisect

WORDLIST = [
    "Football", "Basketball", "Baseball", "Soccer", "Tennis", "Cricket", "Volleyball", 
    "Badminton", "Table Tennis", "Rugby", "Hockey", "Swimming", "Running", "Track and Field",
    "Cycling", "Mountain Biking", "Fitness", "Weightlifting", "CrossFit", "Yoga", "Pilates",
    "Meditation", "Hiking", "Camping", "Backpacking", "Rock Climbing", "Bouldering", "Surfing",
    "Skateboarding", "Rollerblading", "Skiing", "Snowboarding", "Ice Skating", "Golf", "Boxing",
    "MMA", "Karate", "Judo", "Taekwondo", "Fencing", "Archery", "Gymnastics", "Parkour",
    
    "Music", "Rock Music", "Pop Music", "Hip-hop", "Rap", "Classical Music", "Jazz",
    "Electronic Music", "EDM", "Techno", "House Music", "Dubstep", "K-Pop", "Reggae",
    "Metal", "Heavy Metal", "Punk Rock", "Indie Rock", "Blues", "Country Music", "R&B",
    "Soul Music", "Folk Music", "Guitar", "Piano", "Violin", "Drums", "Singing",
    "Songwriting", "Music Production", "DJing", "Beatboxing", "Choir", "Orchestra",
    
    "Anime", "Manga", "Comics", "Graphic Novels", "Marvel", "DC Comics", "Star Wars",
    "Star Trek", "Harry Potter", "Lord of the Rings", "Game of Thrones", "Stranger Things",
    "Netflix", "Disney+", "HBO", "Movies", "Film Making", "Documentaries", "Horror Films",
    "Comedy Movies", "Sci-Fi Movies", "Fantasy Movies", "Action Movies", "Romantic Movies",
    "Bollywood", "K-Dramas", "Theater", "Broadway", "Stand-up Comedy", "Improv",
    
    "Video Games", "PC Gaming", "Console Gaming", "Mobile Gaming", "Fortnite", "Minecraft",
    "League of Legends", "Valorant", "Apex Legends", "Call of Duty", "GTA", "Pokémon",
    "Roblox", "Among Us", "Animal Crossing", "Stardew Valley", "Dota 2", "CS:GO", "Overwatch",
    "World of Warcraft", "Final Fantasy", "Esports", "Speedrunning", "Retro Gaming",
    "VR Gaming", "Streaming", "Twitch", "YouTube", "TikTok", "Instagram", "Social Media",
    "Podcasts", "Vlogging", "Blogging", "Content Creation",
    
    "Photography", "Videography", "Photo Editing", "Video Editing", "Graphic Design",
    "Digital Art", "Illustration", "Drawing", "Sketching", "Painting", "Watercolor",
    "Oil Painting", "Sculpting", "Pottery", "Ceramics", "Woodworking", "Knitting",
    "Crochet", "Sewing", "Embroidery", "Calligraphy", "Hand Lettering", "Writing",
    "Creative Writing", "Poetry", "Journaling", "Screenwriting", "Fan Fiction",
    "Storytelling", "Acting", "Filmmaking", "Animation", "3D Modeling",
    
    "Reading", "Fiction", "Non-fiction Books", "Science Fiction", "Fantasy Books",
    "Mystery Novels", "Romance Novels", "Biographies", "Self-help", "Philosophy",
    "History", "Ancient History", "Military History", "Astronomy", "Astrophysics",
    "Physics", "Quantum Physics", "Chemistry", "Biology", "Genetics", "Neuroscience",
    "Psychology", "Sociology", "Anthropology", "Political Science", "Economics",
    "Mathematics", "Computer Science", "Programming", "Web Development", "App Development",
    "Game Development", "Data Science", "Artificial Intelligence", "Machine Learning",
    "Cybersecurity", "Blockchain", "Cryptocurrency", "Engineering", "Mechanical Engineering",
    "Electrical Engineering", "Robotics", "DIY Projects", "Home Improvement",
    
    "Cooking", "Baking", "Mixology", "Coffee", "Tea", "Wine Tasting", "Beer Brewing",
    "Gardening", "Urban Gardening", "Bonsai", "Aquariums", "Bird Watching", "Fishing",
    "Hunting", "Scuba Diving", "Paragliding", "Skydiving", "Travel", "Backpacking",
    "Language Learning", "Sign Language", "Chess", "Board Games", "Tabletop RPGs",
    "Dungeons & Dragons", "Magic: The Gathering", "Poker", "Cardistry", "Juggling",
    "Origami", "Puzzle Solving", "Collecting", "Vinyl Records", "Coin Collecting",
    "Stamp Collecting", "Fashion", "Streetwear", "Sneakers", "Watch Collecting",
    "Minimalism", "Sustainability", "Volunteering", "Meditation", "Mindfulness",
]

# Normalize, deduplicate, and sort the wordlist for fast search
def get_normalized_wordlist():
    normalized = set(w.strip().lower() for w in WORDLIST if w and isinstance(w, str))
    return sorted(normalized)

NORMALIZED_WORDLIST = get_normalized_wordlist()

# Fast prefix search (returns up to max_results, prefix match prioritized)
def autocomplete_suggestions(query, max_results=15):
    query = query.strip().lower()
    if not query:
        return []
    # Prefix matches
    prefix_matches = [w for w in NORMALIZED_WORDLIST if w.startswith(query)]
    # Substring matches (not prefix)
    substring_matches = [w for w in NORMALIZED_WORDLIST if query in w and not w.startswith(query)]
    results = prefix_matches + substring_matches
    return results[:max_results]

# For Django view usage:
# from .wordlist import autocomplete_suggestions
# suggestions = autocomplete_suggestions(request.GET.get('q', ''))
# return JsonResponse(suggestions, safe=False)
