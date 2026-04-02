from ..lib.db import Base

#  Table tags {
#    id           int       [pk, increment]
#    name         varchar   [unique, not null]
#    post_count   int       [not null, default: 0, note: 'denormalized; updated via content.events']
#    created_at   timestamp
#  }
#  Table post_tags {
#    post_id      int       [not null, note: 'logical ref to Content Service post.id']
#    tag_id       int       [not null, ref: > tags.id]
#    indexes {
#      (post_id, tag_id) [pk]
#      (tag_id, post_id) [note: 'reverse index for feed query']
#    }
#  }
#  Table tag_weight {
#    user_id      int       [not null, note: 'logical ref to User Service users.id']
#    tag_id       int       [not null, ref: > tags.id]
#    weight       float     [not null, default: 0, note: 'like: +1, comment: +5']
#    updated_at   timestamp
#   indexes {
#      (user_id, tag_id) [pk]
#      (user_id, weight) [name: 'idx_user_top_tags', note: 'fast top-K lookup for feed']
#    }
#  }
#  Table post_views {
#    post_id      int       [not null, ref: > post.id]
#    user_id      int       [not null]
#    viewed_at    timestamp
#    indexes {
#      (post_id, user_id) [pk]
#    }
#  }
# famous_tags = (  # noqa E501
#     "trending", "viral", "fyp", "foryoupage", "explore",
#     "reels", "reelsinstagram", "explorepage",
#     "motivation", "inspiration", "mindset", "hustle",
#     "grind", "success", "goals", "lifestyle",
#     "photography", "photooftheday", "aesthetic",
#     "picoftheday", "naturephotography", "portrait",
#     "food", "foodporn", "foodie", "instafood",
#     "homecooking", "foodphotography", "delicious",
#     "fashion", "ootd", "style", "beauty",
#     "makeup", "skincare", "outfitoftheday",
#     "fitness", "gym", "workout", "fitfam",
#     "health", "bodybuilding", "yoga", "running",
#     "travel", "wanderlust", "travelgram", "explore",
#     "adventure", "vacation", "trip", "bucketlist",
#     "music", "newmusic", "hiphop", "pop",
#     "dance", "singer", "artist", "nowplaying",
#     "tech", "startup", "entrepreneur", "ai",
#     "coding", "developer", "business", "innovation",
#     "dogsofinstagram", "catsofinstagram", "nature",
#     "wildlife", "animals", "cute", "pets",
#     "gaming", "gamer", "twitch", "youtube",
#     "esports", "gameplay", "streamer",
#     "love", "happy", "instagood", "follow",
#     "like", "comment", "share", "nofilter",
# )