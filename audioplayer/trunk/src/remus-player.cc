#include <iostream>
#include <vector>
#include <string>

#include <libgnomevfs/gnome-vfs.h>
#include <libgnomevfsmm.h>

extern "C" {
#include <gst/gconf/gconf.h>
#include <gst/play/play.h>
}

#include "remus-player-playlist.h"

int song_nr = 0;
std::vector<std::string> playlist;

static gchar*
get_time_string(time_t seconds)
{
  struct tm *tm = gmtime (&seconds);
  gchar *time;

  time = static_cast<gchar*>(g_malloc (256));

#if 0
  if (seconds > 3600) {
    /* include the hours here */
    if (strftime (time, 256, "%H:%M:%S", tm) <= 0)
      strcpy (time, "--:--:--");
  } else {
    /* just minutes and seconds */
    if (strftime (time, 256, "%M:%S", tm) <= 0)
      strcpy (time, "--:--");
  }
#else
  sprintf(time, "%d", seconds);
#endif
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

  // time_str = get_time_string (seconds);
  // printf("%s\n\033[A", time_str);
  std::cout << time_nanos << std::endl; // << "\033[A";
  g_free(time_str);
}

static void
remus_player_stream_length (GstPlay * play,
			    gint64 length_nanos,
			    gpointer data)
{
  gint seconds;
  gchar *time_str = NULL;

  if (length_nanos) {
    seconds = (gint) (length_nanos / GST_SECOND);
    time_str = get_time_string (seconds);
    // printf("%s\n", time_str);
    std::cout << "Total length: " << time_str << std::endl;
    g_free (time_str);
  }
}


static void
remus_player_stream_end (GstPlay * play, gpointer data)
{
  std::cout << "end of stream called (" << data << ")\n";
  std::cout << gst_play_get_state(play) << std::endl;
  gst_play_set_state (play, GST_STATE_READY);
}

static void
remus_player_error(GstPlay * play, GstElement * element, char *error)
{
  std::cerr << "Pipeline error in " << GST_ELEMENT_NAME(element) << ": "
	    << error << std::endl;
  
}

static void
remus_player_information(GstPlay * play, GstObject * element, GParamSpec * param)
{
  //std::cout << GST_ELEMENT_NAME(element) << "." << g_param_spec_get_name(param)
  //<< " = " << G_PARAM_SPEC_TYPE_NAME(param) << std::endl;
}


static void
remus_player_state_change(GstPlay * play,
			  GstElementState oldstate,
			  GstElementState newstate)
{
  std::cout << "State change: " << gst_element_state_get_name (oldstate)
	    << " -> " << gst_element_state_get_name (newstate) << std::endl;
  if (oldstate == GST_STATE_PAUSED && newstate == GST_STATE_READY)
    if (song_nr < playlist.size()) {
      std::cout << "Song finished!\n";
      std::string song = playlist[song_nr++];
      gst_play_set_location(play, song.c_str());
      gst_play_set_state (play, GST_STATE_PLAYING);
    }
}

static gboolean
remus_player_idle_func(gpointer data)
{
  GstPlay *play = (GstPlay*)data;
}


int
main(int argc, char* argv[])
{
  GstPlay *play;
  GError *error = NULL;
  GstElement *audio_sink;

  gst_init(&argc, &argv);
  Gnome::Vfs::init();

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
  g_signal_connect (G_OBJECT(play), "information",
		    G_CALLBACK(remus_player_information), NULL);
  g_signal_connect (G_OBJECT(play), "state_change",
		    G_CALLBACK(remus_player_state_change), NULL);
  g_signal_connect (G_OBJECT(play), "pipeline_error",
		    G_CALLBACK(remus_player_error), NULL);


  // Add idle function
  play->idle_add_func(remus_player_idle_func, play);


  remus::Playlist plist;
  plist.parse_and_append(argv[1]);
  return 0;
  

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
      playlist.push_back("http://127.0.0.1/music/" + song);
      pos += endofline + 1;
    }
  } else {
    playlist.push_back(argv[1]);
  }
  

  /* FIXME: If input is a sid, set up the pipeline explicitly */
  std::string song = playlist[song_nr++];
  gst_play_set_location(play, song.c_str());

  /* start playing */
  gst_play_set_state (play, GST_STATE_PLAYING);

  gst_main();
  /*  while (gst_bin_iterate (GST_BIN (play->pipeline))); */

  std::cout << "Stop playing...\n";
  /* stop the pipeline */
  gst_play_set_state (play, GST_STATE_NULL);

}
