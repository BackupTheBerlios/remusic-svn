#include <iostream>
#include <vector>
#include <string>

#include <libgnomevfs/gnome-vfs.h>

extern "C" {
#include <gst/gconf/gconf.h>
#include <gst/play/play.h>
}


std::string url_base("http://localhost/music/");
int song_nr = 0;
std::vector<std::string> playlist;


static gchar*
get_time_string(time_t seconds)
{
  struct tm *tm = gmtime (&seconds);
  gchar *time;

  time = static_cast<gchar*>(g_malloc (256));
  if (seconds > 3600) {
    /* include the hours here */
    if (strftime (time, 256, "%H:%M:%S", tm) <= 0)
      strcpy (time, "--:--:--");
  } else {
    /* just minutes and seconds */
    if (strftime (time, 256, "%M:%S", tm) <= 0)
      strcpy (time, "--:--");
  }
  
  return time;
}

static void
remus_player_time_tick (GstPlay * play,
			gint64 time_nanos,
			gpointer data)
{
  gint seconds;
  gchar *time_str = NULL;

  seconds = (gint) (time_nanos / GST_SECOND);

  time_str = get_time_string (seconds);
  // printf("%s\n\033[A", time_str);
  std::cout << time_str << std::endl << "\033[A";
  g_free(time_str);
}

static void
remus_player_stream_length (GstPlay * play,
			    gint64 length_nanos,
			    gpointer data)
{
  gint seconds;
  gchar *time_str = NULL;

  seconds = (gint) (length_nanos / GST_SECOND);
  time_str = get_time_string (seconds);
  // printf("%s\n", time_str);
  std::cout << time_str << std::endl;
  g_free (time_str);
}

int state = 3;

static void
remus_player_stream_end (GstPlay * play, gpointer data)
{
  gst_play_set_state (play, GST_STATE_READY);
  if (--state == 0 && song_nr < playlist.size()) {
    std::cout << "Song finished!\n";
    std::string song = url_base + playlist[song_nr++];
    gst_play_set_location(play, song.c_str());
    gst_play_set_state (play, GST_STATE_PLAYING);
    state = 3;
  }
}

int
main(int argc, char* argv[])
{
  GstPlay *play;
  GError *error = NULL;
  GstElement *audio_sink;

  gst_init(&argc, &argv);

  play = gst_play_new(GST_PLAY_PIPE_AUDIO, &error);
  if (error != NULL) {
    fprintf(stderr, "Error: %s\n", error->message);
    g_error_free(error);
  }
  g_return_val_if_fail(play != NULL, 1);

  audio_sink = gst_gconf_get_default_audio_sink ();
  if (!GST_IS_ELEMENT(audio_sink)) {
    fprintf(stderr,
	    "Error: Could not render default GStreamer audio output sink\n"
	    "from GConf /system/gstreamer/default/audiosink key.\n"
	    "Please verify it is set correctly.\n");
    return 1;
  }

  gst_play_set_audio_sink(play, audio_sink);

  /* Set up signal callbacks */
  
  g_signal_connect (G_OBJECT(play), "stream_length",
		    G_CALLBACK(remus_player_stream_length), NULL);
  g_signal_connect (G_OBJECT(play), "time_tick",
		    G_CALLBACK(remus_player_time_tick), NULL);
  g_signal_connect (G_OBJECT(play), "stream_end",
		    G_CALLBACK(remus_player_stream_end), NULL);
  /*
  g_signal_connect (G_OBJECT(play), "information",
		    G_CALLBACK(remus_player_information), NULL);
  g_signal_connect (G_OBJECT(play), "state_change",
		    G_CALLBACK(remus_player_state_change), NULL);
  g_signal_connect (G_OBJECT(play), "pipeline_error",
		    G_CALLBACK(remus_player_error), NULL);
  */

  /* Is this a playlist? */
  GnomeVFSHandle *filehandle = NULL;
  GnomeVFSResult res = gnome_vfs_open(&filehandle,
				      argv[1],
				      GNOME_VFS_OPEN_READ);

  if (res != GNOME_VFS_OK) {
    std::cerr << "Couldn't open uri:" << gnome_vfs_result_to_string(res);
    return res;
  }

  gchar header[8];
  GnomeVFSFileSize bytes_read;
  res = gnome_vfs_read(filehandle,
		       header,
		       sizeof(header)-1,
		       &bytes_read);

  if (res != GNOME_VFS_OK || bytes_read != sizeof(header)-1) {
    std::cerr << "Couldn't read uri header:"
	      << gnome_vfs_result_to_string(res)
	      << std::endl;
    return res;
  }

  header[sizeof(header)-1] = '\0';
  if (strcmp(header, "#EXTM3U") == 0) {
    GnomeVFSFileInfo fileinfo;
    res = gnome_vfs_get_file_info_from_handle(filehandle,
					      &fileinfo,
					      GNOME_VFS_FILE_INFO_DEFAULT);
    if (res != GNOME_VFS_OK) {
      std::cerr << "Couldn't get size:" << gnome_vfs_result_to_string(res)
		<< std::endl;
      return res;
    }

    g_assert(fileinfo.valid_fields & GNOME_VFS_FILE_INFO_FIELDS_SIZE);

    fileinfo.size -= bytes_read;
    gchar *filebuffer = new gchar[fileinfo.size+1];
    filebuffer[0] = '#';
    int remaining_bytes = fileinfo.size;
    do {
      res = gnome_vfs_read(filehandle,
			   filebuffer + fileinfo.size - remaining_bytes + 1,
			   remaining_bytes, &bytes_read);
      remaining_bytes -= bytes_read;
    } while (bytes_read && remaining_bytes);

    filebuffer[fileinfo.size] = '\0';

    if (res != GNOME_VFS_OK ||
	remaining_bytes != 0 ) {
      std::cerr << "Couldn't read uri:" << gnome_vfs_result_to_string(res)
		<< std::endl;
      std::cerr << "File size: " << fileinfo.size << std::endl;
      std::cerr << "Bytes read: " << bytes_read << std::endl;
      std::cerr << "Bytes I wanted: " << fileinfo.size - sizeof(header) + 1 << std::endl;

      return res;
    }
    int pos = 0;
    int len = strlen(filebuffer);
    while (pos < len) {
      if (filebuffer[pos] == '#') {
	// Skip line
	while (filebuffer[pos++] != '\n')
	  ;
	continue;
      }
      // Song name here, store it in playlist
      int endofline = 0;
      while (pos + endofline < len && filebuffer[pos+endofline] != '\n')
	endofline++;
      std::string song(filebuffer+pos, endofline);
      std::cout << "Found song " << song << std::endl;
      playlist.push_back(song);
      pos += endofline + 1;
    }
  } else {
    playlist.push_back(argv[1]);
  }
  

  /* FIXME: If input is a sid, set up the pipeline explicitly */
  std::string song = url_base + playlist[song_nr++];
  gst_play_set_location(play, song.c_str());

  /* start playing */
  gst_play_set_state (play, GST_STATE_PLAYING);

  gst_main();
  /*  while (gst_bin_iterate (GST_BIN (play->pipeline))); */

  /* stop the pipeline */
  gst_play_set_state (play, GST_STATE_NULL);

}
