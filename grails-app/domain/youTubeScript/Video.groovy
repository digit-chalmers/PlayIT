package youTubeScript

class Video extends MediaItem{

	String title;
	String thumbnail;
	Integer length;
	String description;
	String youtubeID;
	
		
	static constraints = {
		description(maxSize:100000)
	}
}
	
	


	

