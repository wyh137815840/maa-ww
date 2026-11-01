import java.lang.reflect.Method;

/**
 * Give a physical pad back to the main screen after MaaWW left it associated with its
 * virtual display.
 *
 * The association lives in system InputManager (not tied to the caller process), so a killed
 * or restarted MaaWW service can leave the pad stuck on the virtual display. Plain removal does
 * not make InputReader drop the device's cached display, so we first re-associate the pad with
 * the main display (forces a refresh, and is what we want anyway), then remove the association.
 *
 * Run as shell: app_process / PadUnbind <mainDisplayUniqueId> <descriptor> [<descriptor> ...]
 */
public class PadUnbind {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.out.println("usage: PadUnbind <mainDisplayUniqueId> <descriptor>...");
            return;
        }
        String mainUniqueId = args[0];
        Class<?> sm = Class.forName("android.os.ServiceManager");
        Object binder = sm.getMethod("getService", String.class).invoke(null, "input");
        Class<?> stub = Class.forName("android.hardware.input.IInputManager$Stub");
        Object im = stub.getMethod("asInterface", Class.forName("android.os.IBinder")).invoke(null, binder);
        Method add = im.getClass().getMethod("addUniqueIdAssociationByDescriptor", String.class, String.class);
        Method remove = im.getClass().getMethod("removeUniqueIdAssociationByDescriptor", String.class);
        for (int i = 1; i < args.length; i++) {
            String desc = args[i];
            add.invoke(im, desc, mainUniqueId);
            Thread.sleep(400);
            remove.invoke(im, desc);
            System.out.println("released " + desc + " -> main display " + mainUniqueId);
        }
    }
}
