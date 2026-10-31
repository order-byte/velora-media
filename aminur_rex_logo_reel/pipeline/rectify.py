import cv2, numpy as np, sys
S=sys.argv[1]
im=cv2.imread(f'{S}/orig/0121.png')
quad=np.float32([[0,238.7],[720,208.4],[720,804.3],[0,784]])
Ws,Hs=720,570
rect=np.float32([[0,0],[Ws,0],[Ws,Hs],[0,Hs]])
Hq=cv2.getPerspectiveTransform(rect,quad)   # screen -> ref
np.save(f'{S}/Hq.npy',Hq)
inv=np.linalg.inv(Hq)
r=cv2.warpPerspective(im,inv,(Ws,Hs+300),flags=cv2.INTER_CUBIC)
cv2.imwrite(f'{S}/rectified.png',r)
