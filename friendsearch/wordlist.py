
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
    
    # Separate exact, prefix, and substring matches for better sorting
    exact_matches = []
    prefix_matches = []
    substring_matches = []
    
    for word in NORMALIZED_WORDLIST:
        word_lower = word.lower()
        if word_lower == query:
            exact_matches.append(word.title())  # Capitalize for display
        elif word_lower.startswith(query):
            prefix_matches.append(word.title())
        elif query in word_lower:
            substring_matches.append(word.title())
    
    # Combine results with priority: exact > prefix > substring
    # Sort each category by length (shorter first) then alphabetically
    exact_matches.sort(key=lambda x: (len(x), x.lower()))
    prefix_matches.sort(key=lambda x: (len(x), x.lower()))
    substring_matches.sort(key=lambda x: (len(x), x.lower()))
    
    # Combine and limit results
    results = exact_matches + prefix_matches + substring_matches
    return results[:max_results]

# Enhanced search that also handles partial word matching
def enhanced_autocomplete_suggestions(query, max_results=15):
    """
    Enhanced autocomplete that also matches words within compound interests
    e.g., 'rock' matches both 'Rock Music' and 'Rock Climbing'
    """
    query = query.strip().lower()
    if not query:
        return []
    
    matches = []
    query_words = query.split()
    
    for word in WORDLIST:  # Use original wordlist to preserve casing
        word_lower = word.lower()
        word_parts = word_lower.split()
        
        # Calculate match score
        score = 0
        match_type = 'none'
        
        # Exact match (highest priority)
        if word_lower == query:
            score = 1000
            match_type = 'exact'
        # Starts with query (high priority)
        elif word_lower.startswith(query):
            score = 900 - len(word)  # Shorter words ranked higher
            match_type = 'prefix'
        # Any word in the interest starts with query
        elif any(part.startswith(query) for part in word_parts):
            score = 800 - len(word)
            match_type = 'word_prefix'
        # Contains query as substring
        elif query in word_lower:
            score = 700 - len(word)
            match_type = 'substring'
        # Multi-word query: all words found
        elif len(query_words) > 1 and all(any(qw in part for part in word_parts) for qw in query_words):
            score = 600 - len(word)
            match_type = 'multi_word'
        
        if score > 0:
            matches.append((word, score, match_type))
    
    # Sort by score (descending) and limit results
    matches.sort(key=lambda x: (-x[1], len(x[0]), x[0].lower()))
    return [match[0] for match in matches[:max_results]]

# For Django view usage:
# from .wordlist import autocomplete_suggestions
# suggestions = autocomplete_suggestions(request.GET.get('q', ''))
# return JsonResponse(suggestions, safe=False)
