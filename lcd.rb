#!/usr/bin/env ruby
require 'timeout'
require './scroller.rb'

scroller = Scroller.new()

while true
    playlist_entries = `mpc -f '%position%' playlist | tail -n 1`.strip.to_i
    data = `mpc -f '%artist%{///}%title%{///}%album%{///}%name%{///}%file%{///}%position%' current`
    if data != nil
        data = data.strip.split('{///}')
        artist = data[0] || ''
        title = data[1] || ''
        album = data[2] || ''
        name = data[3] || ''
        file = data[4] || ''
        position = data[5] || ''
 #       puts data.join(' /// ')
        if album.empty? && artist.empty?
            scroller.set_line(0, name, file)
        else
            scroller.set_line(0, "#{artist}: #{album}", file)
        end
        line2 = title
        if playlist_entries > 1 && !position.empty?
            line2 = "#{position}. #{line2}"
        end
        scroller.set_line(1, line2, file)
    else
    	scroller.set_line(0, '', '')
    	scroller.set_line(1, '', '')
    end
    scroller.animate()
end

=begin
while true do
    begin
        Timeout::timeout(5) do
            system("mpc --wait -f '[%artist% - %album%\n%title%]|[%name%]' current")
        end
    rescue Timeout::Error => e
        system("mpc -f '[%artist% - %album%\n%title%]|[%name%]' current")
    end
    break
end
=end

