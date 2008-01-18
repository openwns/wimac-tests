set output "posSt.png"
set terminal png
plot 'posSS.junk' using 2:3, 'posBS.junk' using 2:3
#, 'posRS.junk' using 2:3, 'posRMS.junk' using 2:3

#plot 'posBS.junk' using 2:3, 'posSS.junk' using 2:3 , every ::0::0,'posSS.junk' using 2:3 every ::1::1, 'posSS.junk' using 2:3 every ::2::2, 'posSS.junk' using 2:3 every ::3::3, 'posSS.junk' using 2:3 every ::4::4, 'posSS.junk' using 2:3 every ::5::5

#set output "deltaI.png"
#set terminal png
#plot 'output/interference_MAC.Id1_SC1_PDF.dat' using 1:2 title 'deltaInterference_measured-estimated '

#set output "tp.png"
#set terminal png
#plot 'output/