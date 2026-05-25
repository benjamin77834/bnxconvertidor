"""
? BNX V54 GENERATED GLUE JOB
? Generated at: 2026-03-26 19:08:24.168958
"""

from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql.functions import *

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

print("? BNX Glue Job V54 Started")

# =========================
# DAG EXECUTION V54
# =========================

# ? SOURCE: RawUsers
RawUsers_df = spark.read.format("parquet").load("s3://bnx/raw/rawusers")
print("? SOURCE: RawUsers")

# ? SOURCE: RawStreams
RawStreams_df = spark.read.format("parquet").load("s3://bnx/raw/rawstreams")
print("? SOURCE: RawStreams")

# ? SOURCE: RawSongs
RawSongs_df = spark.read.format("parquet").load("s3://bnx/raw/rawsongs")
print("? SOURCE: RawSongs")

# ? SOURCE: RawArtists
RawArtists_df = spark.read.format("parquet").load("s3://bnx/raw/rawartists")
print("? SOURCE: RawArtists")

# ? SOURCE: RawAlbums
RawAlbums_df = spark.read.format("parquet").load("s3://bnx/raw/rawalbums")
print("? SOURCE: RawAlbums")

# ? SOURCE: RawPlaylists
RawPlaylists_df = spark.read.format("parquet").load("s3://bnx/raw/rawplaylists")
print("? SOURCE: RawPlaylists")

# ? SOURCE: RawSubscriptions
RawSubscriptions_df = spark.read.format("parquet").load("s3://bnx/raw/rawsubscriptions")
print("? SOURCE: RawSubscriptions")

# ? SOURCE: RawPayments
RawPayments_df = spark.read.format("parquet").load("s3://bnx/raw/rawpayments")
print("? SOURCE: RawPayments")

# ? SOURCE: RawAds
RawAds_df = spark.read.format("parquet").load("s3://bnx/raw/rawads")
print("? SOURCE: RawAds")

# ? SOURCE: RawDevices
RawDevices_df = spark.read.format("parquet").load("s3://bnx/raw/rawdevices")
print("? SOURCE: RawDevices")

# ? SOURCE: RawSearches
RawSearches_df = spark.read.format("parquet").load("s3://bnx/raw/rawsearches")
print("? SOURCE: RawSearches")

# ? SOURCE: RawSkips
RawSkips_df = spark.read.format("parquet").load("s3://bnx/raw/rawskips")
print("? SOURCE: RawSkips")

# ? SOURCE: RawLikes
RawLikes_df = spark.read.format("parquet").load("s3://bnx/raw/rawlikes")
print("? SOURCE: RawLikes")

# ? SOURCE: RawReports
RawReports_df = spark.read.format("parquet").load("s3://bnx/raw/rawreports")
print("? SOURCE: RawReports")

# ? TRANSFORM: CleanUsers
CleanUsers_df = RawUsers_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanUsers")

# ? TRANSFORM: CleanStreams
CleanStreams_df = RawStreams_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanStreams")

# ? TRANSFORM: CleanSongs
CleanSongs_df = RawSongs_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanSongs")

# ? TRANSFORM: CleanArtists
CleanArtists_df = RawArtists_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanArtists")

# ? TRANSFORM: CleanAlbums
CleanAlbums_df = RawAlbums_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanAlbums")

# ? TRANSFORM: CleanPlaylists
CleanPlaylists_df = RawPlaylists_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanPlaylists")

# ? TRANSFORM: CleanSubscriptions
CleanSubscriptions_df = RawSubscriptions_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanSubscriptions")

# ? TRANSFORM: CleanPayments
CleanPayments_df = RawPayments_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanPayments")

# ? TRANSFORM: CleanAds
CleanAds_df = RawAds_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanAds")

# ? TRANSFORM: CleanDevices
CleanDevices_df = RawDevices_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanDevices")

# ? TRANSFORM: CleanSearches
CleanSearches_df = RawSearches_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanSearches")

# ? TRANSFORM: CleanSkips
CleanSkips_df = RawSkips_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanSkips")

# ? TRANSFORM: CleanLikes
CleanLikes_df = RawLikes_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanLikes")

# ? TRANSFORM: CleanReports
CleanReports_df = RawReports_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: CleanReports")

# ? TRANSFORM: FilterActiveUsers
FilterActiveUsers_df = CleanUsers_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FilterActiveUsers")

# ? JOIN: UserSubscriptionType
UserSubscriptionType_df = FilterActiveUsers_df.join(CleanSubscriptions_df, on="id", how="inner")
print("? JOIN: UserSubscriptionType")

# ? JOIN: UserDeviceHistory
UserDeviceHistory_df = FilterActiveUsers_df.join(CleanDevices_df, on="id", how="inner")
print("? JOIN: UserDeviceHistory")

# ? TRANSFORM: UserListeningHours
UserListeningHours_df = FilterActiveUsers_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: UserListeningHours")

# ? TRANSFORM: UserSkipRate
UserSkipRate_df = FilterActiveUsers_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: UserSkipRate")

# ? JOIN: UserEngagement
UserEngagement_df = UserListeningHours_df.join(UserSkipRate_df, on="id", how="inner")
print("? JOIN: UserEngagement")

# ? JOIN: UserProfile
UserProfile_df = UserSubscriptionType_df.join(UserDeviceHistory_df, on="id", how="inner")
UserProfile_df = UserProfile_df.join(UserEngagement_df, on="id", how="inner")
print("? JOIN: UserProfile")

# ? TRANSFORM: FilterPublishedSongs
FilterPublishedSongs_df = CleanSongs_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FilterPublishedSongs")

# ? JOIN: SongWithArtist
SongWithArtist_df = FilterPublishedSongs_df.join(CleanArtists_df, on="id", how="inner")
print("? JOIN: SongWithArtist")

# ? JOIN: SongWithAlbum
SongWithAlbum_df = SongWithArtist_df.join(CleanAlbums_df, on="id", how="inner")
print("? JOIN: SongWithAlbum")

# ? TRANSFORM: SongPopularity
SongPopularity_df = CleanStreams_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: SongPopularity")

# ? TRANSFORM: SongSkipRate
SongSkipRate_df = CleanSkips_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: SongSkipRate")

# ? TRANSFORM: SongLikeRate
SongLikeRate_df = CleanLikes_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: SongLikeRate")

# ? JOIN: SongScore
SongScore_df = SongPopularity_df.join(SongSkipRate_df, on="id", how="inner")
SongScore_df = SongScore_df.join(SongLikeRate_df, on="id", how="inner")
print("? JOIN: SongScore")

# ? TRANSFORM: TopSongs
TopSongs_df = SongScore_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: TopSongs")

# ? TRANSFORM: BottomSongs
BottomSongs_df = SongScore_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: BottomSongs")

# ? TRANSFORM: FilterCompletedStreams
FilterCompletedStreams_df = CleanStreams_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FilterCompletedStreams")

# ? TRANSFORM: StreamTotals
StreamTotals_df = FilterCompletedStreams_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: StreamTotals")

# ? TRANSFORM: StreamByDevice
StreamByDevice_df = FilterCompletedStreams_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: StreamByDevice")

# ? JOIN: StreamWithUser
StreamWithUser_df = StreamTotals_df.join(UserProfile_df, on="id", how="inner")
print("? JOIN: StreamWithUser")

# ? JOIN: StreamWithSong
StreamWithSong_df = StreamWithUser_df.join(SongWithAlbum_df, on="id", how="inner")
print("? JOIN: StreamWithSong")

# ? JOIN: StreamEnriched
StreamEnriched_df = StreamWithSong_df.join(StreamByDevice_df, on="id", how="inner")
print("? JOIN: StreamEnriched")

# ? TRANSFORM: FilterPublicPlaylists
FilterPublicPlaylists_df = CleanPlaylists_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FilterPublicPlaylists")

# ? TRANSFORM: PlaylistSongCount
PlaylistSongCount_df = FilterPublicPlaylists_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: PlaylistSongCount")

# ? JOIN: PlaylistWithUser
PlaylistWithUser_df = FilterPublicPlaylists_df.join(UserProfile_df, on="id", how="inner")
print("? JOIN: PlaylistWithUser")

# ? JOIN: PlaylistPopularity
PlaylistPopularity_df = PlaylistWithUser_df.join(PlaylistSongCount_df, on="id", how="inner")
print("? JOIN: PlaylistPopularity")

# ? TRANSFORM: TopPlaylists
TopPlaylists_df = PlaylistPopularity_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: TopPlaylists")

# ? TRANSFORM: FilterConfirmedPayments
FilterConfirmedPayments_df = CleanPayments_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FilterConfirmedPayments")

# ? TRANSFORM: RevenueByUser
RevenueByUser_df = FilterConfirmedPayments_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: RevenueByUser")

# ? TRANSFORM: RevenueBySubscription
RevenueBySubscription_df = FilterConfirmedPayments_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: RevenueBySubscription")

# ? TRANSFORM: AdRevenue
AdRevenue_df = CleanAds_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: AdRevenue")

# ? JOIN: AdWithUser
AdWithUser_df = AdRevenue_df.join(UserProfile_df, on="id", how="inner")
print("? JOIN: AdWithUser")

# ? JOIN: TotalRevenue
TotalRevenue_df = RevenueByUser_df.join(RevenueBySubscription_df, on="id", how="inner")
TotalRevenue_df = TotalRevenue_df.join(AdWithUser_df, on="id", how="inner")
print("? JOIN: TotalRevenue")

# ? TRANSFORM: FilterValidSearches
FilterValidSearches_df = CleanSearches_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FilterValidSearches")

# ? TRANSFORM: SearchTrends
SearchTrends_df = FilterValidSearches_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: SearchTrends")

# ? JOIN: SearchWithUser
SearchWithUser_df = FilterValidSearches_df.join(UserProfile_df, on="id", how="inner")
print("? JOIN: SearchWithUser")

# ? JOIN: SearchToStream
SearchToStream_df = SearchWithUser_df.join(StreamEnriched_df, on="id", how="inner")
print("? JOIN: SearchToStream")

# ? TRANSFORM: SearchConversion
SearchConversion_df = SearchToStream_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: SearchConversion")

# ? TRANSFORM: ArtistStreamCount
ArtistStreamCount_df = CleanStreams_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: ArtistStreamCount")

# ? TRANSFORM: ArtistRevenue
ArtistRevenue_df = FilterConfirmedPayments_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: ArtistRevenue")

# ? JOIN: ArtistWithAlbums
ArtistWithAlbums_df = ArtistStreamCount_df.join(CleanAlbums_df, on="id", how="inner")
print("? JOIN: ArtistWithAlbums")

# ? JOIN: ArtistPopularity
ArtistPopularity_df = ArtistWithAlbums_df.join(ArtistRevenue_df, on="id", how="inner")
print("? JOIN: ArtistPopularity")

# ? TRANSFORM: TopArtists
TopArtists_df = ArtistPopularity_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: TopArtists")

# ? TRANSFORM: EmergingArtists
EmergingArtists_df = ArtistPopularity_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: EmergingArtists")

# ? JOIN: FullStreamBase
FullStreamBase_df = StreamEnriched_df.join(TotalRevenue_df, on="id", how="inner")
print("? JOIN: FullStreamBase")

# ? JOIN: EnrichWithRevenue
EnrichWithRevenue_df = FullStreamBase_df.join(TotalRevenue_df, on="id", how="inner")
print("? JOIN: EnrichWithRevenue")

# ? JOIN: EnrichWithSearch
EnrichWithSearch_df = EnrichWithRevenue_df.join(SearchConversion_df, on="id", how="inner")
print("? JOIN: EnrichWithSearch")

# ? JOIN: EnrichWithArtist
EnrichWithArtist_df = EnrichWithSearch_df.join(ArtistPopularity_df, on="id", how="inner")
print("? JOIN: EnrichWithArtist")

# ? TRANSFORM: FlagPowerUser
FlagPowerUser_df = EnrichWithArtist_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FlagPowerUser")

# ? TRANSFORM: FlagChurning
FlagChurning_df = EnrichWithArtist_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FlagChurning")

# ? TRANSFORM: FlagAdTarget
FlagAdTarget_df = EnrichWithArtist_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FlagAdTarget")

# ? TRANSFORM: FlagNewFan
FlagNewFan_df = EnrichWithArtist_df.selectExpr("*")  # no XFR rule found
print("? TRANSFORM: FlagNewFan")

# ? JOIN: MasterReport
MasterReport_df = FlagPowerUser_df.join(FlagChurning_df, on="id", how="inner")
MasterReport_df = MasterReport_df.join(FlagAdTarget_df, on="id", how="inner")
MasterReport_df = MasterReport_df.join(FlagNewFan_df, on="id", how="inner")
print("? JOIN: MasterReport")

# ? SINK: Write_MasterReport
MasterReport_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_masterreport")
print("? SINK: Write_MasterReport")

# ? SINK: Write_PowerUsers
FlagPowerUser_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_powerusers")
print("? SINK: Write_PowerUsers")

# ? SINK: Write_Churning
FlagChurning_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_churning")
print("? SINK: Write_Churning")

# ? SINK: Write_AdTargets
FlagAdTarget_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_adtargets")
print("? SINK: Write_AdTargets")

# ? SINK: Write_NewFans
FlagNewFan_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_newfans")
print("? SINK: Write_NewFans")

# ? SINK: Write_TopSongs
TopSongs_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_topsongs")
print("? SINK: Write_TopSongs")

# ? SINK: Write_BottomSongs
BottomSongs_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_bottomsongs")
print("? SINK: Write_BottomSongs")

# ? SINK: Write_TopPlaylists
TopPlaylists_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_topplaylists")
print("? SINK: Write_TopPlaylists")

# ? SINK: Write_TopArtists
TopArtists_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_topartists")
print("? SINK: Write_TopArtists")

# ? SINK: Write_EmergingArtists
EmergingArtists_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_emergingartists")
print("? SINK: Write_EmergingArtists")

# ? SINK: Write_SearchTrends
SearchTrends_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_searchtrends")
print("? SINK: Write_SearchTrends")

# ? SINK: Write_RevenueReport
TotalRevenue_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_revenuereport")
print("? SINK: Write_RevenueReport")

print("? BNX Glue Job V54 Finished")
