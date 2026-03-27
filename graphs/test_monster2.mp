# ============================================================
# BNX MONSTER 2 - Streaming Media Analytics Platform
# 14 sources, 9 subgraphs, ~90 nodos
# ============================================================

# --- SOURCES (14) ---
NODE RawUsers           : SOURCE
NODE RawStreams         : SOURCE
NODE RawSongs           : SOURCE
NODE RawArtists         : SOURCE
NODE RawAlbums          : SOURCE
NODE RawPlaylists       : SOURCE
NODE RawSubscriptions   : SOURCE
NODE RawPayments        : SOURCE
NODE RawAds             : SOURCE
NODE RawDevices         : SOURCE
NODE RawSearches        : SOURCE
NODE RawSkips           : SOURCE
NODE RawLikes           : SOURCE
NODE RawReports         : SOURCE

# ============================================================
SUBGRAPH Ingestion {
  NODE CleanUsers         : TRANSFORM
  NODE CleanStreams       : TRANSFORM
  NODE CleanSongs         : TRANSFORM
  NODE CleanArtists       : TRANSFORM
  NODE CleanAlbums        : TRANSFORM
  NODE CleanPlaylists     : TRANSFORM
  NODE CleanSubscriptions : TRANSFORM
  NODE CleanPayments      : TRANSFORM
  NODE CleanAds           : TRANSFORM
  NODE CleanDevices       : TRANSFORM
  NODE CleanSearches      : TRANSFORM
  NODE CleanSkips         : TRANSFORM
  NODE CleanLikes         : TRANSFORM
  NODE CleanReports       : TRANSFORM
}

# ============================================================
SUBGRAPH UserDomain {
  NODE FilterActiveUsers      : TRANSFORM
  NODE UserSubscriptionType   : JOIN
  NODE UserDeviceHistory      : JOIN
  NODE UserListeningHours     : TRANSFORM
  NODE UserSkipRate           : TRANSFORM
  NODE UserEngagement         : JOIN
  NODE UserProfile            : JOIN
}

# ============================================================
SUBGRAPH ContentDomain {
  NODE FilterPublishedSongs   : TRANSFORM
  NODE SongWithArtist         : JOIN
  NODE SongWithAlbum          : JOIN
  NODE SongPopularity         : TRANSFORM
  NODE SongSkipRate           : TRANSFORM
  NODE SongLikeRate           : TRANSFORM
  NODE SongScore              : JOIN
  NODE TopSongs               : TRANSFORM
  NODE BottomSongs            : TRANSFORM
}

# ============================================================
SUBGRAPH StreamDomain {
  NODE FilterCompletedStreams  : TRANSFORM
  NODE StreamTotals            : TRANSFORM
  NODE StreamByDevice          : TRANSFORM
  NODE StreamWithUser          : JOIN
  NODE StreamWithSong          : JOIN
  NODE StreamEnriched          : JOIN
}

# ============================================================
SUBGRAPH PlaylistDomain {
  NODE FilterPublicPlaylists  : TRANSFORM
  NODE PlaylistSongCount      : TRANSFORM
  NODE PlaylistWithUser       : JOIN
  NODE PlaylistPopularity     : JOIN
  NODE TopPlaylists           : TRANSFORM
}

# ============================================================
SUBGRAPH RevenueDomain {
  NODE FilterConfirmedPayments : TRANSFORM
  NODE RevenueByUser           : TRANSFORM
  NODE RevenueBySubscription   : TRANSFORM
  NODE AdRevenue               : TRANSFORM
  NODE AdWithUser              : JOIN
  NODE TotalRevenue            : JOIN
}

# ============================================================
SUBGRAPH SearchDomain {
  NODE FilterValidSearches    : TRANSFORM
  NODE SearchTrends           : TRANSFORM
  NODE SearchWithUser         : JOIN
  NODE SearchToStream         : JOIN
  NODE SearchConversion       : TRANSFORM
}

# ============================================================
SUBGRAPH ArtistDomain {
  NODE ArtistStreamCount      : TRANSFORM
  NODE ArtistRevenue          : TRANSFORM
  NODE ArtistWithAlbums       : JOIN
  NODE ArtistPopularity       : JOIN
  NODE TopArtists             : TRANSFORM
  NODE EmergingArtists        : TRANSFORM
}

# ============================================================
SUBGRAPH FinalReport {
  NODE FullStreamBase         : JOIN
  NODE EnrichWithRevenue      : JOIN
  NODE EnrichWithSearch       : JOIN
  NODE EnrichWithArtist       : JOIN
  NODE FlagPowerUser          : TRANSFORM
  NODE FlagChurning           : TRANSFORM
  NODE FlagAdTarget           : TRANSFORM
  NODE FlagNewFan             : TRANSFORM
  NODE MasterReport           : JOIN
}

# ============================================================
# SINKS (12)
NODE Write_MasterReport       : SINK
NODE Write_PowerUsers         : SINK
NODE Write_Churning           : SINK
NODE Write_AdTargets          : SINK
NODE Write_NewFans            : SINK
NODE Write_TopSongs           : SINK
NODE Write_BottomSongs        : SINK
NODE Write_TopPlaylists       : SINK
NODE Write_TopArtists         : SINK
NODE Write_EmergingArtists    : SINK
NODE Write_SearchTrends       : SINK
NODE Write_RevenueReport      : SINK

# ============================================================
# EDGES - Ingestion
# ============================================================
RawUsers          -> CleanUsers
RawStreams        -> CleanStreams
RawSongs          -> CleanSongs
RawArtists        -> CleanArtists
RawAlbums         -> CleanAlbums
RawPlaylists      -> CleanPlaylists
RawSubscriptions  -> CleanSubscriptions
RawPayments       -> CleanPayments
RawAds            -> CleanAds
RawDevices        -> CleanDevices
RawSearches       -> CleanSearches
RawSkips          -> CleanSkips
RawLikes          -> CleanLikes
RawReports        -> CleanReports

# ============================================================
# EDGES - UserDomain
# ============================================================
CleanUsers            -> FilterActiveUsers
FilterActiveUsers     -> UserSubscriptionType
CleanSubscriptions    -> UserSubscriptionType
FilterActiveUsers     -> UserDeviceHistory
CleanDevices          -> UserDeviceHistory
FilterActiveUsers     -> UserListeningHours
FilterActiveUsers     -> UserSkipRate
UserListeningHours    -> UserEngagement
UserSkipRate          -> UserEngagement
UserSubscriptionType  -> UserProfile
UserDeviceHistory     -> UserProfile
UserEngagement        -> UserProfile

# ============================================================
# EDGES - ContentDomain
# ============================================================
CleanSongs            -> FilterPublishedSongs
FilterPublishedSongs  -> SongWithArtist
CleanArtists          -> SongWithArtist
SongWithArtist        -> SongWithAlbum
CleanAlbums           -> SongWithAlbum
CleanStreams          -> SongPopularity
FilterPublishedSongs  -> SongPopularity
CleanSkips            -> SongSkipRate
FilterPublishedSongs  -> SongSkipRate
CleanLikes            -> SongLikeRate
FilterPublishedSongs  -> SongLikeRate
SongPopularity        -> SongScore
SongSkipRate          -> SongScore
SongLikeRate          -> SongScore
SongScore             -> TopSongs
SongScore             -> BottomSongs

# ============================================================
# EDGES - StreamDomain
# ============================================================
CleanStreams           -> FilterCompletedStreams
FilterCompletedStreams -> StreamTotals
FilterCompletedStreams -> StreamByDevice
StreamTotals          -> StreamWithUser
UserProfile           -> StreamWithUser
StreamWithUser        -> StreamWithSong
SongWithAlbum         -> StreamWithSong
StreamWithSong        -> StreamEnriched
StreamByDevice        -> StreamEnriched

# ============================================================
# EDGES - PlaylistDomain
# ============================================================
CleanPlaylists        -> FilterPublicPlaylists
FilterPublicPlaylists -> PlaylistSongCount
FilterPublicPlaylists -> PlaylistWithUser
UserProfile           -> PlaylistWithUser
PlaylistWithUser      -> PlaylistPopularity
PlaylistSongCount     -> PlaylistPopularity
PlaylistPopularity    -> TopPlaylists

# ============================================================
# EDGES - RevenueDomain
# ============================================================
CleanPayments             -> FilterConfirmedPayments
FilterConfirmedPayments   -> RevenueByUser
FilterConfirmedPayments   -> RevenueBySubscription
CleanAds                  -> AdRevenue
AdRevenue                 -> AdWithUser
UserProfile               -> AdWithUser
RevenueByUser             -> TotalRevenue
RevenueBySubscription     -> TotalRevenue
AdWithUser                -> TotalRevenue

# ============================================================
# EDGES - SearchDomain
# ============================================================
CleanSearches         -> FilterValidSearches
FilterValidSearches   -> SearchTrends
FilterValidSearches   -> SearchWithUser
UserProfile           -> SearchWithUser
SearchWithUser        -> SearchToStream
StreamEnriched        -> SearchToStream
SearchToStream        -> SearchConversion

# ============================================================
# EDGES - ArtistDomain
# ============================================================
CleanStreams           -> ArtistStreamCount
CleanArtists          -> ArtistStreamCount
FilterConfirmedPayments -> ArtistRevenue
CleanArtists          -> ArtistRevenue
ArtistStreamCount     -> ArtistWithAlbums
CleanAlbums           -> ArtistWithAlbums
ArtistWithAlbums      -> ArtistPopularity
ArtistRevenue         -> ArtistPopularity
ArtistPopularity      -> TopArtists
ArtistPopularity      -> EmergingArtists

# ============================================================
# EDGES - FinalReport
# ============================================================
StreamEnriched        -> FullStreamBase
TotalRevenue          -> FullStreamBase
FullStreamBase        -> EnrichWithRevenue
TotalRevenue          -> EnrichWithRevenue
EnrichWithRevenue     -> EnrichWithSearch
SearchConversion      -> EnrichWithSearch
EnrichWithSearch      -> EnrichWithArtist
ArtistPopularity      -> EnrichWithArtist
EnrichWithArtist      -> FlagPowerUser
EnrichWithArtist      -> FlagChurning
EnrichWithArtist      -> FlagAdTarget
EnrichWithArtist      -> FlagNewFan
FlagPowerUser         -> MasterReport
FlagChurning          -> MasterReport
FlagAdTarget          -> MasterReport
FlagNewFan            -> MasterReport

# ============================================================
# EDGES - Sinks
# ============================================================
MasterReport          -> Write_MasterReport
FlagPowerUser         -> Write_PowerUsers
FlagChurning          -> Write_Churning
FlagAdTarget          -> Write_AdTargets
FlagNewFan            -> Write_NewFans
TopSongs              -> Write_TopSongs
BottomSongs           -> Write_BottomSongs
TopPlaylists          -> Write_TopPlaylists
TopArtists            -> Write_TopArtists
EmergingArtists       -> Write_EmergingArtists
SearchTrends          -> Write_SearchTrends
TotalRevenue          -> Write_RevenueReport
