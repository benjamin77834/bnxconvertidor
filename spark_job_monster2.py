"""
[*] BNX V54 GENERATED PYSPARK JOB
? Generated at: 2026-09-09 18:18:16.250450
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import StructType

spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()

# =========================
# PARAMETERS
# =========================
class PARAMS:
    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://datalake-bnx-scripts-dev")

print("[*] BNX PySpark Job Started")

# =========================
# HELPER FUNCTIONS
# =========================

def filter_by_expression_hdr_trl(df, field, start, length, exclude_values):
    """Filter rows where substring(field, start, length) is NOT in exclude_values."""
    return df.filter(~F.substring(F.col(field), start, length).isin(exclude_values))


def _bnx_safe_col(df, name, sql):
    """withColumn(name, expr(sql)) tolerante a columnas fuente ausentes."""
    try:
        out = df.withColumn(name, F.expr(sql))
        _ = out.schema  # fuerza el analisis (resuelve nombres) sin ejecutar
        return out
    except Exception as _e:
        _msg = str(_e)
        _cls = type(_e).__name__
        # Columna ausente (UNRESOLVED_COLUMN), SQL malformado (ParseException),
        # funcion inexistente (UNRESOLVED_ROUTINE) o cualquier error de analisis:
        # neutralizar la columna a NULL en vez de tumbar el job.
        if ("UNRESOLVED_COLUMN" in _msg or "cannot be resolved" in _msg
                or "UNRESOLVED_ROUTINE" in _msg or "PARSE_SYNTAX_ERROR" in _msg
                or "ParseException" in _cls or "AnalysisException" in _cls):
            return df.withColumn(name, F.lit(None))
        raise


def _bnx_aggcol(df, name):
    """Resuelve una columna para agregar, tolerante a typo/casing; lit(None) si falta."""
    if df is not None:
        want = name.lower().replace('_', '')
        for c in df.columns:
            if c.lower().replace('_', '') == want:
                return F.col(c)
    return F.lit(None)


def _bnx_ensure_side(df, cols):
    """Asegura que df tenga las columnas dadas (NULL si faltan). Para joins."""
    if df is None:
        return df
    have = set(df.columns)
    for c in cols:
        if c not in have:
            df = df.withColumn(c, F.lit(None).cast('string'))
    return df


def is_valid_record(df, validation_rules=None):
    """Validate records. Returns tuple: (valid_df, invalid_df)"""
    if validation_rules is None:
        return df, spark.createDataFrame([], df.schema)
    condition = None
    for rule in validation_rules:
        field = rule["field"]
        rule_type = rule.get("type", "not_null")
        if rule_type == "not_null":
            c = F.col(field).isNotNull()
        elif rule_type == "length":
            c = F.length(F.col(field)) <= rule["max_length"]
        elif rule_type == "range":
            c = (F.col(field) >= rule["min"]) & (F.col(field) <= rule["max"])
        elif rule_type == "in_list":
            c = F.col(field).isin(rule["values"])
        else:
            continue
        condition = c if condition is None else condition & c
    if condition is None:
        return df, spark.createDataFrame([], df.schema)
    return df.filter(condition), df.filter(~condition)


def output_indexes_split(df, index_expr, num_outputs):
    """Split DataFrame into N outputs based on index expression."""
    return [df.filter(F.expr(f"{index_expr} = {i}")) for i in range(num_outputs)]


# =========================
# DAG EXECUTION V54
# =========================

# [+] SOURCE: RawAds
RawAds_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawads")
print("[>] SOURCE: RawAds")

# [.] TRANSFORM: CleanAds
CleanAds_df = RawAds_df.selectExpr("ad_id", "user_id", "campaign_id", "impressions", "clicks", "revenue", "ad_date")
CleanAds_df = CleanAds_df.where("ad_id IS NOT NULL")
print("[~] TRANSFORM: CleanAds")

# [.] TRANSFORM: AdRevenue
AdRevenue_df = CleanAds_df.groupBy("user_id", "campaign_id").agg(sum(_bnx_aggcol(CleanAds_df, "revenue")).alias("ad_revenue"), sum(_bnx_aggcol(CleanAds_df, "impressions")).alias("total_impressions"), sum(_bnx_aggcol(CleanAds_df, "clicks")).alias("total_clicks"))
print("[~] TRANSFORM: AdRevenue")

# [+] SOURCE: RawUsers
RawUsers_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawusers")
print("[>] SOURCE: RawUsers")

# [.] TRANSFORM: CleanUsers
CleanUsers_df = RawUsers_df.selectExpr("user_id", "username", "email", "country", "plan_type", "created_at")
CleanUsers_df = CleanUsers_df.where("user_id IS NOT NULL")
print("[~] TRANSFORM: CleanUsers")

# [.] TRANSFORM: FilterActiveUsers
FilterActiveUsers_df = CleanUsers_df.selectExpr("*")
FilterActiveUsers_df = FilterActiveUsers_df.where("plan_type != 'cancelled'")
print("[~] TRANSFORM: FilterActiveUsers")

# [+] SOURCE: RawSubscriptions
RawSubscriptions_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawsubscriptions")
print("[>] SOURCE: RawSubscriptions")

# [.] TRANSFORM: CleanSubscriptions
CleanSubscriptions_df = RawSubscriptions_df.selectExpr("subscription_id", "user_id", "plan_type", "start_date", "end_date", "active")
CleanSubscriptions_df = CleanSubscriptions_df.where("subscription_id IS NOT NULL")
print("[~] TRANSFORM: CleanSubscriptions")

# [~] JOIN: UserSubscriptionType
UserSubscriptionType_df = FilterActiveUsers_df.join(CleanSubscriptions_df, on=["user_id"], how="left")
print("[~] JOIN: UserSubscriptionType")

# [+] SOURCE: RawDevices
RawDevices_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawdevices")
print("[>] SOURCE: RawDevices")

# [.] TRANSFORM: CleanDevices
CleanDevices_df = RawDevices_df.selectExpr("device_id", "user_id", "device_type", "os", "last_active")
CleanDevices_df = CleanDevices_df.where("device_id IS NOT NULL")
print("[~] TRANSFORM: CleanDevices")

# [~] JOIN: UserDeviceHistory
UserDeviceHistory_df = FilterActiveUsers_df.join(CleanDevices_df, on=["user_id"], how="left")
print("[~] JOIN: UserDeviceHistory")

# [.] TRANSFORM: UserListeningHours
UserListeningHours_df = FilterActiveUsers_df.groupBy("user_id").agg(sum(_bnx_aggcol(FilterActiveUsers_df, "duration_sec")).alias("total_listen_sec"), count(_bnx_aggcol(FilterActiveUsers_df, "stream_id")).alias("stream_count"))
print("[~] TRANSFORM: UserListeningHours")

# [.] TRANSFORM: UserSkipRate
UserSkipRate_df = FilterActiveUsers_df.groupBy("user_id").agg(count(_bnx_aggcol(FilterActiveUsers_df, "skip_id")).alias("skip_count"), avg(_bnx_aggcol(FilterActiveUsers_df, "skip_time_sec")).alias("avg_skip_sec"))
print("[~] TRANSFORM: UserSkipRate")

# [~] JOIN: UserEngagement
UserEngagement_df = UserListeningHours_df.join(UserSkipRate_df, on=["user_id"], how="inner")
print("[~] JOIN: UserEngagement")

# [~] JOIN: UserProfile
UserProfile_df = UserSubscriptionType_df.join(UserDeviceHistory_df, on=["user_id"], how="left")
UserProfile_df = UserProfile_df.join(UserEngagement_df, on=["user_id"], how="left")
print("[~] JOIN: UserProfile")

# [~] JOIN: AdWithUser
AdWithUser_df = AdRevenue_df.join(UserProfile_df, on=["user_id"], how="left")
print("[~] JOIN: AdWithUser")

# [+] SOURCE: RawStreams
RawStreams_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawstreams")
print("[>] SOURCE: RawStreams")

# [.] TRANSFORM: CleanStreams
CleanStreams_df = RawStreams_df.selectExpr("stream_id", "user_id", "song_id", "device_id", "duration_sec", "completed", "streamed_at")
CleanStreams_df = CleanStreams_df.where("stream_id IS NOT NULL AND duration_sec > 0")
print("[~] TRANSFORM: CleanStreams")

# [+] SOURCE: RawArtists
RawArtists_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawartists")
print("[>] SOURCE: RawArtists")

# [.] TRANSFORM: CleanArtists
CleanArtists_df = RawArtists_df.selectExpr("artist_id", "name", "country", "genre", "verified", "joined_at")
CleanArtists_df = CleanArtists_df.where("artist_id IS NOT NULL")
print("[~] TRANSFORM: CleanArtists")

# [.] TRANSFORM: ArtistStreamCount
ArtistStreamCount_df = CleanStreams_df.groupBy("artist_id").agg(count(_bnx_aggcol(CleanStreams_df, "stream_id")).alias("artist_streams"), sum(_bnx_aggcol(CleanStreams_df, "duration_sec")).alias("artist_listen_sec"))
print("[~] TRANSFORM: ArtistStreamCount")

# [+] SOURCE: RawAlbums
RawAlbums_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawalbums")
print("[>] SOURCE: RawAlbums")

# [.] TRANSFORM: CleanAlbums
CleanAlbums_df = RawAlbums_df.selectExpr("album_id", "title", "artist_id", "release_date", "track_count")
CleanAlbums_df = CleanAlbums_df.where("album_id IS NOT NULL")
print("[~] TRANSFORM: CleanAlbums")

# [~] JOIN: ArtistWithAlbums
ArtistWithAlbums_df = ArtistStreamCount_df.join(CleanAlbums_df, on=["artist_id"], how="left")
print("[~] JOIN: ArtistWithAlbums")

# [+] SOURCE: RawPayments
RawPayments_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawpayments")
print("[>] SOURCE: RawPayments")

# [.] TRANSFORM: CleanPayments
CleanPayments_df = RawPayments_df.selectExpr("payment_id", "user_id", "amount", "method", "payment_date", "confirmed")
CleanPayments_df = CleanPayments_df.where("confirmed = true")
print("[~] TRANSFORM: CleanPayments")

# [.] TRANSFORM: FilterConfirmedPayments
FilterConfirmedPayments_df = CleanPayments_df.selectExpr("*")
FilterConfirmedPayments_df = FilterConfirmedPayments_df.where("confirmed = true")
print("[~] TRANSFORM: FilterConfirmedPayments")

# [.] TRANSFORM: ArtistRevenue
ArtistRevenue_df = FilterConfirmedPayments_df.groupBy("artist_id").agg(sum(_bnx_aggcol(FilterConfirmedPayments_df, "amount")).alias("artist_revenue"), count(_bnx_aggcol(FilterConfirmedPayments_df, "payment_id")).alias("artist_payments"))
print("[~] TRANSFORM: ArtistRevenue")

# [~] JOIN: ArtistPopularity
ArtistPopularity_df = ArtistWithAlbums_df.join(ArtistRevenue_df, on=["artist_id"], how="left")
print("[~] JOIN: ArtistPopularity")

# [+] SOURCE: RawSongs
RawSongs_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawsongs")
print("[>] SOURCE: RawSongs")

# [.] TRANSFORM: CleanSongs
CleanSongs_df = RawSongs_df.selectExpr("song_id", "title", "artist_id", "album_id", "genre", "duration_sec", "release_date", "published")
CleanSongs_df = CleanSongs_df.where("song_id IS NOT NULL")
print("[~] TRANSFORM: CleanSongs")

# [.] TRANSFORM: FilterPublishedSongs
FilterPublishedSongs_df = CleanSongs_df.selectExpr("*")
FilterPublishedSongs_df = FilterPublishedSongs_df.where("published = true")
print("[~] TRANSFORM: FilterPublishedSongs")

# [.] TRANSFORM: SongPopularity
SongPopularity_df = CleanStreams_df.groupBy("song_id").agg(count(_bnx_aggcol(CleanStreams_df, "stream_id")).alias("play_count"), sum(_bnx_aggcol(CleanStreams_df, "duration_sec")).alias("total_play_sec"))
print("[~] TRANSFORM: SongPopularity")

# [+] SOURCE: RawSkips
RawSkips_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawskips")
print("[>] SOURCE: RawSkips")

# [.] TRANSFORM: CleanSkips
CleanSkips_df = RawSkips_df.selectExpr("skip_id", "user_id", "song_id", "skip_time_sec", "skipped_at")
CleanSkips_df = CleanSkips_df.where("skip_id IS NOT NULL")
print("[~] TRANSFORM: CleanSkips")

# [.] TRANSFORM: SongSkipRate
SongSkipRate_df = CleanSkips_df.groupBy("song_id").agg(count(_bnx_aggcol(CleanSkips_df, "skip_id")).alias("song_skip_count"))
print("[~] TRANSFORM: SongSkipRate")

# [+] SOURCE: RawLikes
RawLikes_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawlikes")
print("[>] SOURCE: RawLikes")

# [.] TRANSFORM: CleanLikes
CleanLikes_df = RawLikes_df.selectExpr("like_id", "user_id", "song_id", "liked_at")
CleanLikes_df = CleanLikes_df.where("like_id IS NOT NULL")
print("[~] TRANSFORM: CleanLikes")

# [.] TRANSFORM: SongLikeRate
SongLikeRate_df = CleanLikes_df.groupBy("song_id").agg(count(_bnx_aggcol(CleanLikes_df, "like_id")).alias("song_like_count"))
print("[~] TRANSFORM: SongLikeRate")

# [~] JOIN: SongScore
SongScore_df = SongPopularity_df.join(SongSkipRate_df, on=["song_id"], how="left")
SongScore_df = SongScore_df.join(SongLikeRate_df, on=["song_id"], how="left")
print("[~] JOIN: SongScore")

# [.] TRANSFORM: BottomSongs
BottomSongs_df = SongScore_df.selectExpr("*")
BottomSongs_df = BottomSongs_df.where("play_count < 10 AND song_skip_count > 5")
print("[~] TRANSFORM: BottomSongs")

# [+] SOURCE: RawPlaylists
RawPlaylists_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawplaylists")
print("[>] SOURCE: RawPlaylists")

# [.] TRANSFORM: CleanPlaylists
CleanPlaylists_df = RawPlaylists_df.selectExpr("playlist_id", "user_id", "name", "is_public", "song_count", "created_at")
CleanPlaylists_df = CleanPlaylists_df.where("playlist_id IS NOT NULL")
print("[~] TRANSFORM: CleanPlaylists")

# [+] SOURCE: RawReports
RawReports_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawreports")
print("[>] SOURCE: RawReports")

# [.] TRANSFORM: CleanReports
CleanReports_df = RawReports_df.selectExpr("report_id", "user_id", "song_id", "reason", "reported_at")
CleanReports_df = CleanReports_df.where("report_id IS NOT NULL")
print("[~] TRANSFORM: CleanReports")

# [+] SOURCE: RawSearches
RawSearches_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/rawsearches")
print("[>] SOURCE: RawSearches")

# [.] TRANSFORM: CleanSearches
CleanSearches_df = RawSearches_df.selectExpr("search_id", "user_id", "query", "results_count", "clicked", "searched_at")
CleanSearches_df = CleanSearches_df.where("search_id IS NOT NULL")
print("[~] TRANSFORM: CleanSearches")

# [.] TRANSFORM: EmergingArtists
EmergingArtists_df = ArtistPopularity_df.selectExpr("*")
EmergingArtists_df = EmergingArtists_df.where("artist_streams > 500 AND artist_streams < 5000")
print("[~] TRANSFORM: EmergingArtists")

# [.] TRANSFORM: FilterCompletedStreams
FilterCompletedStreams_df = CleanStreams_df.selectExpr("*")
FilterCompletedStreams_df = FilterCompletedStreams_df.where("completed = true")
print("[~] TRANSFORM: FilterCompletedStreams")

# [.] TRANSFORM: StreamTotals
StreamTotals_df = FilterCompletedStreams_df.groupBy("user_id", "song_id").agg(sum(_bnx_aggcol(FilterCompletedStreams_df, "duration_sec")).alias("total_duration"), count(_bnx_aggcol(FilterCompletedStreams_df, "stream_id")).alias("stream_count"))
print("[~] TRANSFORM: StreamTotals")

# [~] JOIN: StreamWithUser
StreamWithUser_df = StreamTotals_df.join(UserProfile_df, on=["user_id"], how="inner")
print("[~] JOIN: StreamWithUser")

# [~] JOIN: SongWithArtist
SongWithArtist_df = FilterPublishedSongs_df.join(CleanArtists_df, on=["artist_id"], how="left")
print("[~] JOIN: SongWithArtist")

# [~] JOIN: SongWithAlbum
SongWithAlbum_df = SongWithArtist_df.join(CleanAlbums_df, on=["album_id"], how="left")
print("[~] JOIN: SongWithAlbum")

# [~] JOIN: StreamWithSong
StreamWithSong_df = StreamWithUser_df.join(SongWithAlbum_df, on=["song_id"], how="left")
print("[~] JOIN: StreamWithSong")

# [.] TRANSFORM: StreamByDevice
StreamByDevice_df = FilterCompletedStreams_df.groupBy("device_id").agg(count(_bnx_aggcol(FilterCompletedStreams_df, "stream_id")).alias("device_stream_count"), sum(_bnx_aggcol(FilterCompletedStreams_df, "duration_sec")).alias("device_total_sec"))
print("[~] TRANSFORM: StreamByDevice")

# [~] JOIN: StreamEnriched
StreamEnriched_df = StreamWithSong_df.join(StreamByDevice_df, on=["device_id"], how="left")
print("[~] JOIN: StreamEnriched")

# [.] TRANSFORM: RevenueByUser
RevenueByUser_df = FilterConfirmedPayments_df.groupBy("user_id").agg(sum(_bnx_aggcol(FilterConfirmedPayments_df, "amount")).alias("user_revenue"), count(_bnx_aggcol(FilterConfirmedPayments_df, "payment_id")).alias("payment_count"))
print("[~] TRANSFORM: RevenueByUser")

# [.] TRANSFORM: RevenueBySubscription
RevenueBySubscription_df = FilterConfirmedPayments_df.groupBy("plan_type", "user_id").agg(sum(_bnx_aggcol(FilterConfirmedPayments_df, "amount")).alias("plan_revenue"), count(_bnx_aggcol(FilterConfirmedPayments_df, "user_id")).alias("subscriber_count"))
print("[~] TRANSFORM: RevenueBySubscription")

# [~] JOIN: TotalRevenue
TotalRevenue_df = RevenueByUser_df.join(RevenueBySubscription_df, on=["user_id"], how="left")
TotalRevenue_df = TotalRevenue_df.join(AdWithUser_df, on=["user_id"], how="left")
print("[~] JOIN: TotalRevenue")

# [~] JOIN: FullStreamBase
FullStreamBase_df = StreamEnriched_df.join(TotalRevenue_df, on=["user_id"], how="left")
print("[~] JOIN: FullStreamBase")

# [~] JOIN: EnrichWithRevenue
EnrichWithRevenue_df = FullStreamBase_df.join(TotalRevenue_df, on=["user_id"], how="left")
print("[~] JOIN: EnrichWithRevenue")

# [.] TRANSFORM: FilterValidSearches
FilterValidSearches_df = CleanSearches_df.selectExpr("*")
FilterValidSearches_df = FilterValidSearches_df.where("results_count > 0")
print("[~] TRANSFORM: FilterValidSearches")

# [~] JOIN: SearchWithUser
SearchWithUser_df = FilterValidSearches_df.join(UserProfile_df, on=["user_id"], how="left")
print("[~] JOIN: SearchWithUser")

# [~] JOIN: SearchToStream
SearchToStream_df = SearchWithUser_df.join(StreamEnriched_df, on=["user_id"], how="left")
print("[~] JOIN: SearchToStream")

# [.] TRANSFORM: SearchConversion
SearchConversion_df = SearchToStream_df.groupBy("user_id").agg(count(_bnx_aggcol(SearchToStream_df, "search_id")).alias("searches"), sum(_bnx_aggcol(SearchToStream_df, "clicked")).alias("search_clicks"))
print("[~] TRANSFORM: SearchConversion")

# [~] JOIN: EnrichWithSearch
EnrichWithSearch_df = EnrichWithRevenue_df.join(SearchConversion_df, on=["user_id"], how="left")
print("[~] JOIN: EnrichWithSearch")

# [~] JOIN: EnrichWithArtist
EnrichWithArtist_df = EnrichWithSearch_df.join(ArtistPopularity_df, on=["artist_id"], how="left")
print("[~] JOIN: EnrichWithArtist")

# [.] TRANSFORM: FilterPublicPlaylists
FilterPublicPlaylists_df = CleanPlaylists_df.selectExpr("*")
FilterPublicPlaylists_df = FilterPublicPlaylists_df.where("is_public = true")
print("[~] TRANSFORM: FilterPublicPlaylists")

# [.] TRANSFORM: FlagAdTarget
FlagAdTarget_df = EnrichWithArtist_df.selectExpr("*")
FlagAdTarget_df = FlagAdTarget_df.where("ad_revenue > 0 AND total_impressions > 100")
print("[~] TRANSFORM: FlagAdTarget")

# [.] TRANSFORM: FlagChurning
FlagChurning_df = EnrichWithArtist_df.selectExpr("*")
FlagChurning_df = FlagChurning_df.where("stream_count < 5 AND skip_count > 10")
print("[~] TRANSFORM: FlagChurning")

# [.] TRANSFORM: FlagNewFan
FlagNewFan_df = EnrichWithArtist_df.selectExpr("*")
FlagNewFan_df = FlagNewFan_df.where("stream_count > 50 AND stream_count < 200")
print("[~] TRANSFORM: FlagNewFan")

# [.] TRANSFORM: FlagPowerUser
FlagPowerUser_df = EnrichWithArtist_df.selectExpr("*")
FlagPowerUser_df = FlagPowerUser_df.where("total_listen_sec > 360000 AND stream_count > 500")
print("[~] TRANSFORM: FlagPowerUser")

# [~] JOIN: MasterReport
MasterReport_df = FlagPowerUser_df.join(FlagChurning_df, on=["user_id"], how="left")
MasterReport_df = MasterReport_df.join(FlagAdTarget_df, on=["user_id"], how="left")
MasterReport_df = MasterReport_df.join(FlagNewFan_df, on=["user_id"], how="left")
print("[~] JOIN: MasterReport")

# [~] JOIN: PlaylistWithUser
PlaylistWithUser_df = FilterPublicPlaylists_df.join(UserProfile_df, on=["user_id"], how="left")
print("[~] JOIN: PlaylistWithUser")

# [.] TRANSFORM: PlaylistSongCount
PlaylistSongCount_df = FilterPublicPlaylists_df.groupBy("playlist_id").agg(sum(_bnx_aggcol(FilterPublicPlaylists_df, "song_count")).alias("total_songs"))
print("[~] TRANSFORM: PlaylistSongCount")

# [~] JOIN: PlaylistPopularity
PlaylistPopularity_df = PlaylistWithUser_df.join(PlaylistSongCount_df, on=["playlist_id"], how="left")
print("[~] JOIN: PlaylistPopularity")

# [.] TRANSFORM: SearchTrends
SearchTrends_df = FilterValidSearches_df.groupBy("query").agg(count(_bnx_aggcol(FilterValidSearches_df, "search_id")).alias("search_count"), avg(_bnx_aggcol(FilterValidSearches_df, "results_count")).alias("avg_results"))
print("[~] TRANSFORM: SearchTrends")

# [.] TRANSFORM: TopArtists
TopArtists_df = ArtistPopularity_df.selectExpr("*")
TopArtists_df = TopArtists_df.where("artist_streams > 10000")
print("[~] TRANSFORM: TopArtists")

# [.] TRANSFORM: TopPlaylists
TopPlaylists_df = PlaylistPopularity_df.selectExpr("*")
TopPlaylists_df = TopPlaylists_df.where("total_songs > 50")
print("[~] TRANSFORM: TopPlaylists")

# [.] TRANSFORM: TopSongs
TopSongs_df = SongScore_df.selectExpr("*")
TopSongs_df = TopSongs_df.where("play_count > 1000")
print("[~] TRANSFORM: TopSongs")

# [*] SINK: Write_AdTargets
Write_AdTargets_df = FlagAdTarget_df
write_adtargets_df = FlagAdTarget_df
FlagAdTarget_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_adtargets")
print("[>] SINK: Write_AdTargets")

# [*] SINK: Write_BottomSongs
Write_BottomSongs_df = BottomSongs_df
write_bottomsongs_df = BottomSongs_df
BottomSongs_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_bottomsongs")
print("[>] SINK: Write_BottomSongs")

# [*] SINK: Write_Churning
Write_Churning_df = FlagChurning_df
write_churning_df = FlagChurning_df
FlagChurning_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_churning")
print("[>] SINK: Write_Churning")

# [*] SINK: Write_EmergingArtists
Write_EmergingArtists_df = EmergingArtists_df
write_emergingartists_df = EmergingArtists_df
EmergingArtists_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_emergingartists")
print("[>] SINK: Write_EmergingArtists")

# [*] SINK: Write_MasterReport
Write_MasterReport_df = MasterReport_df
write_masterreport_df = MasterReport_df
MasterReport_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_masterreport")
print("[>] SINK: Write_MasterReport")

# [*] SINK: Write_NewFans
Write_NewFans_df = FlagNewFan_df
write_newfans_df = FlagNewFan_df
FlagNewFan_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_newfans")
print("[>] SINK: Write_NewFans")

# [*] SINK: Write_PowerUsers
Write_PowerUsers_df = FlagPowerUser_df
write_powerusers_df = FlagPowerUser_df
FlagPowerUser_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_powerusers")
print("[>] SINK: Write_PowerUsers")

# [*] SINK: Write_RevenueReport
Write_RevenueReport_df = TotalRevenue_df
write_revenuereport_df = TotalRevenue_df
TotalRevenue_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_revenuereport")
print("[>] SINK: Write_RevenueReport")

# [*] SINK: Write_SearchTrends
Write_SearchTrends_df = SearchTrends_df
write_searchtrends_df = SearchTrends_df
SearchTrends_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_searchtrends")
print("[>] SINK: Write_SearchTrends")

# [*] SINK: Write_TopArtists
Write_TopArtists_df = TopArtists_df
write_topartists_df = TopArtists_df
TopArtists_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_topartists")
print("[>] SINK: Write_TopArtists")

# [*] SINK: Write_TopPlaylists
Write_TopPlaylists_df = TopPlaylists_df
write_topplaylists_df = TopPlaylists_df
TopPlaylists_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_topplaylists")
print("[>] SINK: Write_TopPlaylists")

# [*] SINK: Write_TopSongs
Write_TopSongs_df = TopSongs_df
write_topsongs_df = TopSongs_df
TopSongs_df.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/write_topsongs")
print("[>] SINK: Write_TopSongs")

spark.stop()
print("[ok] BNX PySpark Job Finished")
