class Scroller
    def initialize()
        @width = 40
        @height = 2
        @lines = [] 
        @offset = []
        @tag = []
        @height.times { @lines << ''; @offset << 0; @tag << '' }
    end
    
    def set_line(y, s, tag)
        if tag == @tag[y]
            return if @offset[y] > 0
        end
        s = '' if s == nil
        if s != @lines[y]
            @lines[y] = s
            @offset[y] = -20
        end
        @tag[y] = tag
    end
    
    def render()
        system('clear')
        @lines.each_with_index do |line, index|
            cropped = line
            if line.size > @width
                cropped += ' +++ '
                cropped += line
            end
            offset = @offset[index]
            offset = 0 if offset < 0
            cropped += ' ' * @width
            cropped = cropped[offset, @width]
            puts cropped
        end
    end

    def animate()
        render()
        sleep(0.1)
        @lines.each_with_index do |line, index|
            if line.size <= @width
                @offset[index] = 0
            else
                @offset[index] += 1
                if @offset[index] == line.size + 5
                    @offset[index] = -20
                end
            end
        end
    end
end
